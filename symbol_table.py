from errors import SemanticError

class SymbolTable:
    """
    Symbol table for FORTRAN77 compiler.
    Manages variable declarations, types, initialization status, and unique identifiers.
    Follows the pattern from sexp_plus example.
    """
    
    def __init__(self):
        self.__table = {}
        self.__current_scope = 'GLOBAL'
        self.__all_scopes = {
                'GLOBAL': {
                    'name': 'GLOBAL',
                    'vars': self.__table,
                    'prev': None,
                    'type': 'PROGRAM',
                    'return_address': None
                }
            }
        self.__scope_stack = ['GLOBAL'] # stack dos nomes dos scopes
        self.__current_scope = 'GLOBAL'
        self.calls_to_verify = [] # para guardar as chamadas de funções/subrotinas que não estão na symbol table no momento da análise semântica, para verificar no final se estão declaradas
                                    # (node, symbol_table_entry)
        self.gotos_to_verify = [] # para guardar os GOTO targets que não estão na symbol table no momento da análise semântica, para verificar no final se estão declarados

    def __repr__(self):
        return self.__table.__repr__()

    def symbols(self):
        """Return all declared symbols in current scope."""
        return self.__table.keys()

    def lookup(self, name):
        """
        Look up a symbol in the table.
        Returns symbol information or raises SemanticError if undeclared.
        """
        if name not in self.__table:
            raise SemanticError(f"Undeclared variable: {name}")
        return self.__table[name]

    def declare(self, name, var_type=None, is_array=False, size=None, is_parameter=False, is_formal_param=False, value=None, is_label=False, is_return_value=False):
        """
        Declare a new identifier with optional type and array information.
        Raises SemanticError if variable is already declared.
        """
        existing_symbol = self.__table.get(name)
        if existing_symbol is not None:
            
            if existing_symbol['is_formal_param'] and existing_symbol['type'] is None:
                existing_symbol['type'] = var_type
                if is_array: existing_symbol['is_array'] = is_array
                if size: existing_symbol['size'] = size
                existing_symbol['initialized'] = True # parâmetros formais são considerados inicializados para permitir atribuição de outros parâmetros a eles
                return # Exit successfully
            if existing_symbol['is_label'] and is_label:
                raise SemanticError(f"Duplicate label: {name}")
            
            raise SemanticError(f"Duplicate declaration: {name}")
        
        if self.get_current_scope_type() == 'FUNCTION' and name == self.get_current_scope_name() and not is_return_value:
            raise SemanticError(f"Function '{name}' cannot declare a variable with the same name as the function itself.")

        idx = len(self.__table)
        self.__table[name] = {
            'index': idx,
            'type': var_type,  # INTEGER, REAL, LOGICAL, DOUBLE, CHARACTER
            'initialized': False,
            'is_array': is_array,
            'size': size,
            'is_parameter': is_parameter,
            'is_formal_param': is_formal_param, # params na declaração de funcoes
            'is_return_value': is_return_value, # for functions
            'is_label': is_label, # for labels
            'value': value 
        }
        
    def get_index(self, name):
        if name not in self.__table:
            raise SemanticError(f"Undeclared variable: {name}")
        return self.__table[name]['index']
    
    def initialize(self, name):
        """
        Mark a variable as initialized.
        Raises SemanticError if variable is not declared.
        """
        if name not in self.__table:
            raise SemanticError(f"Undeclared variable: {name}")
        self.__table[name]['initialized'] = True

    def set_value(self, name, value, index=None):
            
        if name not in self.__table:
            if self.get_current_scope_type() == 'FUNCTION' and name == self.get_current_scope_name():
                self.declare(name, var_type=self.get_current_scope_type(), is_return_value=True)
                scope_name = self.get_current_scope_name() 
                self.__all_scopes[scope_name]['return_value_assigned'] = True # marcar que o return value já foi atribuído em algum ponto do código 
            else:
                raise SemanticError(f"Symbol '{name}' not declared.")
        
        self.check_parameter_assignment(name)
        if self.__table[name]['is_label']:
            raise SemanticError(name + " isn't a variable.")
        
        if self.__table[name]['is_array']:
            if index is None:
                raise SemanticError(f"Must provide an index to assign a value to array variable '{name}'.")
            if not isinstance(index, int):
                # caso seja uma expressão verifica só o tipo
                index_type = self.get_expr_type(index)
                if index_type != 'INTEGER':
                    raise SemanticError(f"Array index for variable '{name}' must be of type INTEGER, got {index_type}.")
            else:
                #senão verifica se o index é válido para o tamanho do array
                self.check_array_access(name, index)

        value_type = self.get_expr_type(value)
        var_type = self.__table[name]['type']
        if not self.is_type_compatible(value_type, var_type) and not self.get_current_scope_type() == 'FUNCTION':
            raise SemanticError(f"Type mismatch: cannot assign value of type {value_type} to variable '{name}' of type {var_type}.")
        if self.get_current_scope_type() == 'FUNCTION' and name == self.get_current_scope_name() and not self.is_type_compatible(value_type, self.get_return_type(self.get_current_scope_name())):
            raise SemanticError(f"Type mismatch: cannot assign value of type {value_type} to return variable '{name}' of type {self.get_return_type(self.get_current_scope_name())}.")
        
        self.initialize(name) # marcar a variável como inicializada e verificar se foi declarada

        if not isinstance(value, tuple): # se for atómico, pode guardar o valor para otimizações futuras
            self.__table[name]['value'] = value

    def is_type_compatible(self, type1, type2):
        """Check if the type of the value is compatible with the variable's declared type."""
        if type1 == 'INTEGER' and type2 == 'INTEGER':
            return True
        elif type1 == 'REAL' and type2 in ['REAL', 'INTEGER']:
            return True
        elif type1 == 'LOGICAL' and type2 == 'LOGICAL':
            return True
        elif type1 in ['CHARACTER', 'STRING'] and type2 == 'CHARACTER':
            return True
        elif type1 == 'DOUBLE' and type2 in ['DOUBLE', 'REAL', 'INTEGER']:
            return True
        elif type1 in ['REAL', 'DOUBLE'] and type2 in ['REAL', 'DOUBLE', 'INTEGER']:
            return True
        return False

    def get_type(self, name):
        """Get the type of a variable."""
        if name not in self.__table:
            raise SemanticError(f"Symbol '{name}' not declared.")
        return self.__table[name]['type']

    def get_value(self, name):
        """Get the value of a parameter or constant."""
        if name not in self.__table:
            raise SemanticError(f"Symbol '{name}' not declared.")
        return self.__table[name].get('value', None)

    def is_initialized(self, name):
        """Check if a variable has been initialized."""
        if name not in self.__table:
            raise SemanticError(f"Symbol '{name}' not declared.")
        return self.__table[name]['initialized']

    def is_array(self, name):
        """Check if a variable is an array."""
        if name not in self.__table:
            raise SemanticError(f"Symbol '{name}' not declared.")
        return self.__table[name]['is_array']

    def is_return_value(self, name):
        """Check if a variable is the return value of a function."""
        if name not in self.__table:
            raise SemanticError(f"Symbol '{name}' not declared.")
        return self.__table[name]['is_return_value']
    
    def set_return_address(self, scope_name, address):
        """Set the return address for a scope's return value."""
        if scope_name not in self.__all_scopes:
            raise SemanticError(f"Scope '{scope_name}' not found.")
        self.__all_scopes[scope_name]['return_address'] = address

    def get_size(self, name):
        """Get the size of an array variable."""
        if name not in self.__table:
            raise SemanticError(f"Symbol '{name}' not declared.")
        if not self.__table[name]['is_array']:
            raise SemanticError(f"Variable '{name}' is not an array.")
        return self.__table[name]['size']

    def get_expr_type(self, node):
        # Se for um valor atómico (INT, REAL, BOOL, STRING)
        if isinstance(node, bool): return 'LOGICAL'
        if isinstance(node, int): return 'INTEGER'
        if isinstance(node, float): return 'REAL'
        if isinstance(node, str):
            if node[0] == '\'' and node[-1] == '\'':
                if len(node) == 3:
                    return 'CHARACTER'
                else: 
                    return 'STRING'

            # senão é string ou char é var       
              
            if node not in self.__table or self.__table[node]['initialized'] == False:
                raise SemanticError(f"Undeclared or uninitialized variable: '{node}'.")
            if self.__table[node]['type'] is None:
                raise SemanticError(f"Variable '{node}' has no declared type.")
            return self.__table[node]['type']

        # tuplo
        op = node[0]
        if op == 'INDEX_OR_CALL': # aceder a um array ou chamar função/subrotina -> tem de estar declarada no scope atual, senão erro
            name = node[1]
            if name in self.__table:
                if self.__table[name]['is_array']:
                    if len(node[2]) != 1:
                        raise SemanticError(f"Array variable '{name}' accessed with wrong number of indices- only ")
                    self.check_array_access(name, node[2][0]) 
                    if self.__table[name]['type'] is None:
                        raise SemanticError(f"Array variable '{name}' has no declared type.")
                    return self.__table[name]['type']
                else:
                # aqui assume-se que é uma função/subrotina 
                # se estiver na scope list, pode-se fazer a verificação de tipo e número de args
                    if self.get_scope_type(name):
                        self.check_is_function(name)
                        self.check_call_args(name, [self.get_expr_type(arg) for arg in node[2]])
                        return self.get_return_type(name)
                # senão, tem de se fazer essa verificação no final -> guardar no calls to verify
                    self.calls_to_verify.append((node, self.get_current_scope_name()))
                    return 'INTEGER' # tipo genérico para permitir a análise semântica continuar, a verificação real do tipo é feita no final da análise semântica
            else:
                raise SemanticError(f"Symbol '{name}' not declared.")

        if op in ['ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'POWER']:
            t1 = self.get_expr_type(node[1])
            t2 = self.get_expr_type(node[2])
            if t1 == 'REAL' or t2 == 'REAL': return 'REAL'
            return 'INTEGER'
        
        if op in ['LT', 'GT', 'EQ', 'NE', 'LE', 'GE']:
            t1 = self.get_expr_type(node[1])
            t2 = self.get_expr_type(node[2])
            numericos = ['INTEGER', 'REAL']
            strings = ['CHARACTER', 'STRING']
            if (t1 in numericos and t2 in numericos) or (t1 in strings and t2 in strings):
                return 'LOGICAL'
            else:
                raise SemanticError(f"Operação {op} inválida entre {t1} e {t2}")
            
        if op in ['AND', 'OR']:
            t1 = self.get_expr_type(node[1])
            t2 = self.get_expr_type(node[2])
            if t1 == t2 == 'LOGICAL':
                return 'LOGICAL'
            else:
                raise SemanticError(f"Operação {op} inválida entre {t1} e {t2}")
            
        if op == 'NOT':
            t = self.get_expr_type(node[1])
            if t == 'LOGICAL':
                return 'LOGICAL'
            else:
                raise SemanticError(f"Operação NOT inválida sobre {t}")
        
        if op == 'CONCAT':
            t1 = self.get_expr_type(node[1])
            t2 = self.get_expr_type(node[2])
            if t1 in ['CHARACTER', 'STRING'] and t2 in ['CHARACTER', 'STRING']:
                return 'STRING'
            else:
                raise SemanticError(f"Operação {op} inválida entre {t1} e {t2}")
        return None
    
    def is_constant_expression(self, node):
        if isinstance(node, (int, float, bool)): # literais
            return True
        
        if isinstance(node, tuple):
            # Se for uma operação como ADD, SUB, MUL...
            # A expressão só é constante se todos os seus operandos forem constantes
            if node[0] in ['ADD', 'SUB', 'MUL', 'DIV', 'POWER']:
                return self.is_constant_expression(node[1]) and \
                    self.is_constant_expression(node[2])
            
            if node[0] == 'INDEX_OR_CALL': # não podem ser chamadas de funções 
                return False

        # 3. Se for uma string (nome de identificador)
        if isinstance(node, str):
            var_info = self.symbol_table.lookup(node)
            # SÓ é constante se o identificador for outro PARAMETER
            if var_info and var_info.get('is_parameter'):
                return True
            return False

        return False
    
    def push_scope(self, scope_name, scope_type, return_type=None):
        """Create new scope and switch to it."""

        #se existe função/subrotina com mesmo nome do scope atual print de warning
        if scope_name in self.__all_scopes:
            raise SemanticError(f"Duplicate function/subroutine/program name: {scope_name}")

        if scope_type == 'FUNCTION' and return_type is None:
            raise SemanticError(f"Function '{scope_name}' must have a return type.")
        
        # atualiza a tabela do vars do prev
        self.__all_scopes[self.__scope_stack[-1]]['vars'] = self.__table

        self.__table = {}
        new_scope = {
            'name': scope_name,
            'vars': self.__table,
            'prev': self.__scope_stack[-1],
            'type': scope_type,
            'return_type': return_type,
            'return_value_assigned': False, # para funções - se o return value já foi atribuído em algum ponto do código
            'return_address': None # translator phase -> onde guardar o return val scom o storel
        }
        self.__all_scopes[scope_name] = new_scope
        self.__scope_stack.append(scope_name)
        self.__current_scope = scope_name

    def pop_scope(self):
        """Go to previous scope."""
        if len(self.__scope_stack) > 1:

            # se for func e não houve nenhum value assignment print de warning. limitações: não verifica IFs
            if not self.is_return_value_assigned():
                print(f"Warning: Function '{self.__scope_stack[-1]}' has no return value assigned.")


            self.__scope_stack.pop()
            self.__current_scope = self.__scope_stack[-1]
            self.__table = self.__all_scopes[self.__scope_stack[-1]]['vars']
            return True
        return False
    
    def get_scope_type(self, scope_name):
        """Get the type of a scope (PROGRAM, FUNCTION, SUBROUTINE)."""
        if scope_name not in self.__all_scopes:
            raise SemanticError(f"Scope '{scope_name}' not found. (1)")
        return self.__all_scopes[scope_name]['type']

    def set_scope_return_type(self, return_type):
        """Set the return type for the current scope (used for functions)."""
        self.__all_scopes[self.__current_scope]['return_type'] = return_type
    
    def set_scope_return_address(self, address):
        """Set the return address for the current scope (used for function return values)."""
        self.__all_scopes[self.__current_scope]['return_address'] = address
    
    def is_return_value_assigned(self):
        """Check if the return value of the current function scope has been assigned."""
        if self.get_current_scope_type() not in ['FUNCTION']:
            return True # não precisa de return value
        return self.__all_scopes[self.__current_scope]['return_value_assigned']

    def get_current_scope_name(self):
        """Get the name of the current scope."""
        return self.__current_scope
    
    def get_current_scope_type(self):
        """Get the type of the current scope."""
        return self.__all_scopes[self.__current_scope]['type']
        
    # para declarar no inicio do scope em codigo maquina
    def get_table(self, scope_name):
        """Get the symbol table for a specific scope."""
        if scope_name not in self.__all_scopes:
            raise SemanticError(f"Scope '{scope_name}' not found (2).")
        return self.__all_scopes[scope_name]['vars']
    
    def get_return_type(self, scope_name):
        """Get the return type of a function."""
        if scope_name not in self.__all_scopes:
            raise SemanticError(f"Scope '{scope_name}' not found (3).")
        return self.__all_scopes[scope_name]['return_type']
    
    def get_return_address(self, scope_name):
        """Get the return address for a function's return value."""
        if scope_name not in self.__all_scopes:
            raise SemanticError(f"Scope '{scope_name}' not found (4).")
        return self.__all_scopes[scope_name]['return_address']
        
    def check_array_access(self, name, index= None):
        """Check if an array variable is accessed with a valid index."""
        if name not in self.__table:
            raise SemanticError(f"Undeclared variable: '{name}'.")
        if not self.__table[name]['is_array']:
            raise SemanticError(f"Variable '{name}' is not an array.")
        if index is not None:
            if isinstance(index, int):
                size = self.__table[name]['size']
                if index < 1 or index > size:
                    raise SemanticError(f"Array index out of bounds for variable '{name}': {index} (size: {size}).")
                else:
                    raise SemanticError(f"Array index for variable '{name}' must be an integer.")
    
    def check_parameter_assignment(self, name):
        """Check if a parameter is being assigned a value after declaration."""
        if name not in self.__table:
            raise SemanticError(f"Undeclared variable: '{name}'.")
        if self.__table[name]['is_parameter']:
            raise SemanticError(f"Cannot assign a value to parameter '{name}' after declaration.")
        

    def add_subroutine_call(self, name, arglist):
        """Check if a subroutine call is valid or add it to the list of calls to verify."""
        if name in self.__all_scopes:
            self.check_is_subroutine(name)
            self.check_call_args(name, [self.get_expr_type(arg) for arg in arglist])
        else:
            self.calls_to_verify.append((name, arglist))
        
    def check_call_args(self, scope_name, args_types):
        """Verificar número e tipos dos argumentos numa chamada de função/subrotina."""
        if scope_name not in self.__all_scopes:
            raise SemanticError(f"Undefined function/subroutine: '{scope_name}'.")
        
        scope_vars = self.__all_scopes[scope_name]['vars']
        # Verificar os parâmetros formais na ordem correta (index) para comparar com os argumentos fornecidos
        formal_params = sorted(
            [(n, v) for n, v in scope_vars.items() if v['is_formal_param']],
            key=lambda x: x[1]['index']
        )
        
        if len(args_types) != len(formal_params):
            raise SemanticError(
                f"Wrong number of arguments for '{scope_name}': "
                f"expected {len(formal_params)}, got {len(args_types)}."
            )
        
        for (param_name, param_info), arg_type in zip(formal_params, args_types):
            param_type = param_info['type']
            if param_type is None:
                continue  # ignorar
            # numeric = {'INTEGER', 'REAL', 'DOUBLE'}
            # # permitir promoção numérica
            # if param_type in numeric and arg_type in numeric:
            #     continue
            if param_type != arg_type:
                raise SemanticError(
                    f"Type mismatch in argument '{param_name}' of '{scope_name}': "
                    f"expected {param_type}, got {arg_type}."
                )

    def check_function_exists(self, name):
        """Verificar que uma função/subrotina foi declarada."""
        if name not in self.__all_scopes:
            return False
        return True
    
    def get_scope_type(self, scope_name):
        """Get the type of a scope (PROGRAM, FUNCTION, SUBROUTINE)."""
        if scope_name not in self.__all_scopes:
            return None
        return self.__all_scopes[scope_name]['type']
        
    def check_is_subroutine(self, name):
        """Verificar que o CALL é feito a uma subrotina e não a uma função."""
        if name not in self.__all_scopes:
            raise SemanticError(f"Undefined subroutine: '{name}'.")
        if self.__all_scopes[name]['type'] != 'SUBROUTINE':
            raise SemanticError(f"'{name}' is a FUNCTION, not a SUBROUTINE. Use it as an expression, not with CALL.")

    def check_is_function(self, name):
        """Verificar que uma chamada de expressão é a uma função e não a uma subrotina."""
        if name not in self.__all_scopes:
            return  # pode ser função intrínseca (ABS, MOD, etc.) — ignorar
        if self.__all_scopes[name]['type'] != 'FUNCTION':
            raise SemanticError(f"'{name}' is a SUBROUTINE and cannot be used as an expression.")
            
    def declare_label(self, label, statement = None):
        """Declarar um label (ex: 100 CONTINUE)."""
        label_key = f"__label_{label}"
        if label_key in self.__table:
            raise SemanticError(f"Duplicate label: {label}.")
        self.__table[label_key] = {
            'index': None,
            'type': 'LABEL',
            'initialized': True,
            'is_array': False,
            'size': None,
            'is_parameter': False,
            'is_formal_param': False,
            'is_return_value': False,
            'is_label': True,
            'value': label,
            'statement': statement

        }

    def check_label_exists(self, label):
        """Verificar que um label alvo de GOTO foi declarado."""
        label_key = f"__label_{label}"
        if label_key not in self.__table:
            raise SemanticError(f"GOTO target label {label} is not defined in this scope.")

    def check_label_is_continue(self, label):
        """Verificar que um label é de um CONTINUE"""
        label_key = f"__label_{label}"
        if label_key not in self.__table:
            raise SemanticError(f"DO target label {label} is not defined in this scope.")
            
        statement = self.__table[label_key].get('statement')
        
        if not isinstance(statement, tuple) or statement[0] != 'CONTINUE':
            raise SemanticError(f"DO target label {label} does not correspond to a CONTINUE statement.")

    def register_goto_label(self, label):
        """Guarda um GOTO para ser verificado no fim do scope."""
        if label not in self.__table:
            self.gotos_to_verify.append((self.get_current_scope_name(), label))
        elif not self.__table[label]['is_label']:
            raise SemanticError(f"GOTO or DO target '{label}' is not a label.")

    def verify_pending_gotos(self):
        """Verifica se todos os GOTO apontam para labels existentes no respetivo scope."""
        errors = []
        current_table = self.__table # guardar a tabela atual para voltar a ela 

        for scope_name, label in self.gotos_to_verify:
            self.__table = self.__all_scopes[scope_name]['vars'] # mudar para a tabela do scope onde o GOTO foi declarado
            try:
                self.check_label_exists(label)
            except SemanticError as e:
                errors.append(str(e))

        self.__table = current_table # voltar à tabela original
        
        if errors:
            raise SemanticError("\n".join(errors))

    def check_do_loop(self, var_name, start_type, end_type, step_type=None):
        """Verificar que a variável de controlo do DO é inteira e os limites são numéricos."""
        if var_name not in self.__table:
            raise SemanticError(f"Undeclared DO loop variable: '{var_name}'.")
        
        var_type = self.__table[var_name]['type']
        if var_type not in ('INTEGER', None):
            raise SemanticError(f"DO loop variable '{var_name}' must be INTEGER, got {var_type}.")
        
        numeric = {'INTEGER', 'REAL', 'DOUBLE'}
        if start_type not in numeric:
            raise SemanticError(f"DO loop start value must be numeric, got {start_type}.")
        if end_type not in numeric:
            raise SemanticError(f"DO loop end value must be numeric, got {end_type}.")
        if step_type is not None and step_type not in numeric:
            raise SemanticError(f"DO loop step value must be numeric, got {step_type}.")
        if step_type == 'INTEGER' and step_type == 0:
            raise SemanticError("DO loop step cannot be zero.")
        
    def verify_pending_calls(self):
        """Verificar no final se as chamadas guardadas são válidas, mudando de scope se necessário."""
        errors = []
        
        # Salvar o scope original (geralmente 'GLOBAL') para restaurar no fim
        original_scope_name = self.__scope_stack[-1]

        for node, scope_name in self.calls_to_verify:
            name = node[1] # 'CONVRT'
            args = node[2] # ['NUM', 'BASE']
            
            # 1. Mudar temporariamente a tabela para o scope onde a chamada ocorreu
            # Isto faz com que get_expr_type encontre 'NUM' e 'BASE'
            if scope_name in self.__all_scopes:
                self.__table = self.__all_scopes[scope_name]['vars']
            
            # 2. Verificar se a função existe na globalidade do programa
            if name not in self.__all_scopes:
                errors.append(f"Undefined function/subroutine: '{name}'.")
                continue
            
            try:
                # 3. Resolver os tipos dos argumentos usando a tabela do scope da chamada
                args_types = [self.get_expr_type(arg) for arg in args]
                
                # 4. Validar se é função/subrotina e se os argumentos batem
                if node[0] == 'INDEX_OR_CALL':
                    self.check_is_function(name)
                elif node[0] == 'CALL':
                    self.check_is_subroutine(name)
                    
                self.check_call_args(name, args_types)
                
            except SemanticError as e:
                errors.append(str(e))
                
        # Restaurar a tabela para o scope original
        self.__table = self.__all_scopes[original_scope_name]['vars']
        
        if errors:
            raise SemanticError("\n".join(errors))
        
    def go_to_scope(self, scope_name):
        if scope_name is None:
            scope_name = 'GLOBAL'
        if scope_name not in self.__all_scopes:
            raise SemanticError(f"Scope '{scope_name}' not found.")
        self.__current_scope = scope_name
        self.__table = self.__all_scopes[scope_name]['vars']
                
            
        
