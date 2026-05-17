from errors import SemanticError

class SymbolTable:
    def __init__(self):
        """Inicializa a tabela de símbolos e as estruturas de scopes/pendências."""
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
        self.do_labels_to_verify = [] 

    def lookup(self, name):
        """Procura um símbolo no scope atual e lança erro se não existir."""
        if name not in self.__table:
            raise SemanticError(f"Undeclared variable: {name}")
        return self.__table[name]

    def declare(self, name, var_type=None, is_array=False, size=None, is_parameter=False, is_formal_param=False, value=None, is_label=False, is_return_value=False):
        """Declara um símbolo no scope atual, validando duplicados e casos especiais."""
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
            'type': var_type,
            'initialized': False,
            'is_array': is_array,
            'size': size,
            'is_parameter': is_parameter,
            'is_formal_param': is_formal_param,
            'is_return_value': is_return_value,
            'is_label': is_label,
            'value': value 
        }
        
    def get_index(self, name):
        """Devolve o índice (endereço) de um símbolo no scope atual."""
        if name not in self.__table:
            raise SemanticError(f"Undeclared variable: {name}")
        return self.__table[name]['index']
    
    def initialize(self, name):
        """Marca um símbolo como inicializado, validando que existe."""
        if name not in self.__table:
            raise SemanticError(f"Undeclared variable: {name}")
        self.__table[name]['initialized'] = True

    def set_value(self, name, value, index=None):
        """Atribui valor a uma variável/array e valida declaração, índices e tipos."""
            
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
                if not self.__table[name]['type'] == "CHARACTER":
                    raise SemanticError(f"Must provide an index to assign a value to array variable '{name}'.")
                
                if not self.is_type_compatible(self.__table[name]['type'], self.get_expr_type(value)):
                    raise SemanticError(f"Type mismatch: cannot assign value of type {self.get_expr_type(value)} to array variable '{name}' of type CHARACTER.")
                
                self.initialize(name) # marcar a variável como inicializada e verificar se foi declarada
                if not isinstance(value, tuple): 
                    self.__table[name]['value'] = value
                return
            
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
        if not self.is_type_compatible(var_type, value_type) and not self.get_current_scope_type() == 'FUNCTION':
            raise SemanticError(f"Type mismatch: cannot assign value of type {value_type} to variable '{name}' of type {var_type}.")
        if self.get_current_scope_type() == 'FUNCTION' and name == self.get_current_scope_name() and not self.is_type_compatible(value_type, self.get_return_type(self.get_current_scope_name())):
            raise SemanticError(f"Type mismatch: cannot assign value of type {value_type} to return variable '{name}' of type {self.get_return_type(self.get_current_scope_name())}.")
        
        self.initialize(name) # marcar a variável como inicializada e verificar se foi declarada

        if not isinstance(value, tuple): # se for atómico, pode guardar o valor para otimizações futuras
            self.__table[name]['value'] = value

    def is_type_compatible(self, type1, type2):
        """Verifica compatibilidade entre o tipo declarado e o tipo do valor."""
        if type1 == 'INTEGER' and type2 == 'INTEGER':
            return True
        elif type1 == 'REAL' and type2 in ['REAL', 'INTEGER']:
            return True
        elif type1 == 'LOGICAL' and type2 == 'LOGICAL':
            return True
        elif type1 == 'CHARACTER' and type2 in ['CHARACTER', 'STRING']:
            return True
        elif type1 == 'STRING' and type2 in ['CHARACTER', 'STRING']:
            return True
        return False

    def get_type(self, name):
        """Devolve o tipo declarado de um símbolo."""
        if name not in self.__table:
            raise SemanticError(f"Symbol '{name}' not declared.")
        return self.__table[name]['type']

    def get_value(self, name):
        """Devolve o valor guardado (ex.: PARAMETER), se existir."""
        if name not in self.__table:
            raise SemanticError(f"Symbol '{name}' not declared.")
        return self.__table[name].get('value', None)
    

    def is_initialized(self, name):
        """Indica se um símbolo já foi inicializado."""
        if name not in self.__table:
            raise SemanticError(f"Symbol '{name}' not declared.")
        return self.__table[name]['initialized']

    def is_array(self, name):
        """Indica se um símbolo é um array."""
        if name not in self.__table:
            raise SemanticError(f"Symbol '{name}' not declared.")
        return self.__table[name]['is_array']

    def is_return_value(self, name):
        """Indica se o símbolo representa o valor de retorno de uma função."""
        if name not in self.__table:
            raise SemanticError(f"Symbol '{name}' not declared.")
        return self.__table[name]['is_return_value']
    
    def set_return_address(self, scope_name, address):
        """Define o endereço relativo ao scope da função onde o retorno da função deve ser guardado no código máquina."""
        if scope_name not in self.__all_scopes:
            raise SemanticError(f"Scope '{scope_name}' not found.")
        self.__all_scopes[scope_name]['return_address'] = address

    def get_size(self, name):
        """Devolve o tamanho de um array."""
        if name not in self.__table:
            raise SemanticError(f"Symbol '{name}' not declared.")
        if not self.__table[name]['is_array']:
            raise SemanticError(f"Variable '{name}' is not an array.")
        return self.__table[name]['size']

    def get_expr_type(self, node):
        """Infere o tipo de uma expressão, valida uso de símbolos/índices/chamadas e compatibilidade em expressões."""
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
            if node not in self.__table or self.__table[node]['initialized'] == False and not self.__table[node]['is_parameter'] and not self.__table[node]['is_array']:
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
                        raise SemanticError(f"Array variable '{name}' accessed with wrong number of indices: expected 1, got {len(node[2])}.")
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
            if t1 not in ['INTEGER', 'REAL'] or t2 not in ['INTEGER', 'REAL']:
                raise SemanticError(f"Operation {op} not possible between {t1} and {t2}.")
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
                raise SemanticError(f"Operation {op} invalid between {t1} e {t2}")
            
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
        """Indica se a expressão é constante (literais/parameters e operações entre estes)."""
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
            try:
                var_info = self.lookup(node)
            except SemanticError:
                return False
            
            # SÓ é constante se o identificador for outro PARAMETER
            if var_info and var_info.get('is_parameter'):
                return True
            return False
        return False
    
    def push_scope(self, scope_name, scope_type, return_type=None):
        """Cria um novo scope e muda o contexto de análise para esse scope."""

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
        """Volta ao scope anterior e restaura a tabela desse scope."""
        if len(self.__scope_stack) > 1:

            # se for func e não houve nenhum value assignment print de warning. limitações: não verifica IFs
            if not self.is_return_value_assigned():
                print(f"Warning: Function '{self.__scope_stack[-1]}' has no return value assigned.")
                
            # verificar e limpar os GOTOs pendentes do scope que está a fechar
            self.__scope_stack.pop()
            self.__current_scope = self.__scope_stack[-1]
            self.__table = self.__all_scopes[self.__scope_stack[-1]]['vars']
            return True
        return False
    
    def get_scope_type(self, scope_name):
        """Devolve o tipo de um scope (PROGRAM/FUNCTION/SUBROUTINE) ou erro."""
        if scope_name not in self.__all_scopes:
            raise SemanticError(f"Scope '{scope_name}' not found. (1)")
        return self.__all_scopes[scope_name]['type']

    def set_scope_return_type(self, return_type):
        """Define o tipo de retorno do scope atual (para funções)."""
        self.__all_scopes[self.__current_scope]['return_type'] = return_type
    
    def set_scope_return_address(self, address):
        """Define o endereço de retorno no scope atual (para funções)."""
        self.__all_scopes[self.__current_scope]['return_address'] = address
    
    def is_return_value_assigned(self):
        """Indica se a função atual já atribuiu o seu valor de retorno."""
        if self.get_current_scope_type() not in ['FUNCTION']:
            return True # não precisa de return value
        return self.__all_scopes[self.__current_scope]['return_value_assigned']

    def get_current_scope_name(self):
        """Devolve o nome do scope atual."""
        return self.__current_scope
    
    def get_current_scope_type(self):
        """Devolve o tipo do scope atual."""
        return self.__all_scopes[self.__current_scope]['type']
        
    # para declarar no inicio do scope em codigo maquina
    def get_table(self, scope_name):
        """Devolve a tabela de símbolos (vars) de um scope."""
        if scope_name not in self.__all_scopes:
            raise SemanticError(f"Scope '{scope_name}' not found (2).")
        return self.__all_scopes[scope_name]['vars']
    
    def get_return_type(self, scope_name):
        """Devolve o tipo de retorno de uma função."""
        if scope_name not in self.__all_scopes:
            raise SemanticError(f"Scope '{scope_name}' not found (3).")
        return self.__all_scopes[scope_name]['return_type']
    
    def get_return_address(self, scope_name):
        """Devolve o endereço onde o retorno da função deve ser guardado."""
        if scope_name not in self.__all_scopes:
            raise SemanticError(f"Scope '{scope_name}' not found (4).")
        return self.__all_scopes[scope_name]['return_address']
        
    def check_array_access(self, name, index= None):
        """Valida acesso a array (tipo e limites do índice)."""
        if name not in self.__table:
            raise SemanticError(f"Undeclared variable: '{name}'.")
        if not self.__table[name]['is_array']:
            raise SemanticError(f"Variable '{name}' is not an array.")
        if index is None:
            return
        
        if isinstance(index, int):
            size = self.__table[name]['size']
            if index < 1 or index > size:
                raise SemanticError(
                    f"Array index out of bounds for variable '{name}': {index} (size: {size})."
                )
            return
        index_type = self.get_expr_type(index)
        if index_type != 'INTEGER':
            raise SemanticError(
                f"Array index for variable '{name}' must be of type INTEGER, got {index_type}."
            )
    
    def check_parameter_assignment(self, name):
        """Impede atribuições a PARAMETERs."""
        if name not in self.__table:
            raise SemanticError(f"Undeclared variable: '{name}'.")
        if self.__table[name]['is_parameter']:
            raise SemanticError(f"Cannot assign a value to parameter '{name}' after declaration.")
        

    def add_subroutine_call(self, node):
        """Valida um CALL imediato ou guarda a chamada em calls_to_verify para verificação posterior."""
        name, arglist = node[1], node[2]
        if name in self.__all_scopes:
            self.check_is_subroutine(name)
            self.check_call_args(name, [self.get_expr_type(arg) for arg in arglist])
        else:
            self.calls_to_verify.append((('CALL', name, arglist), self.get_current_scope_name()))
        
    def check_call_args(self, scope_name, args_types):
        """Verifica número e tipos dos argumentos numa chamada."""
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
                continue
            if param_type != arg_type:
                raise SemanticError(
                    f"Type mismatch in argument '{param_name}' of '{scope_name}': "
                    f"expected {param_type}, got {arg_type}."
                )

    def check_function_exists(self, name):
        """Indica se uma função/subrotina foi declarada."""
        if name not in self.__all_scopes:
            return False
        return True
    
    def get_scope_type(self, scope_name):
        """Devolve o tipo de um scope ou None se não existir."""
        if scope_name not in self.__all_scopes:
            return None
        return self.__all_scopes[scope_name]['type']
        
    def check_is_subroutine(self, name):
        """Verifica que o nome se refere uma subrotina.""" # para a CALL
        if name not in self.__all_scopes:
            raise SemanticError(f"Undefined subroutine: '{name}'.")
        if self.__all_scopes[name]['type'] != 'SUBROUTINE':
            raise SemanticError(f"'{name}' is a FUNCTION, not a SUBROUTINE. Use it as an expression, not with CALL.")

    def check_is_function(self, name):
        """Verifica que o nome refere uma função.""" # para chamadas em expressões indexorcall
        if name not in self.__all_scopes:
            return  # pode ser função intrínseca (ABS, MOD, etc.) — ignorar
        if self.__all_scopes[name]['type'] != 'FUNCTION':
            raise SemanticError(f"'{name}' is a SUBROUTINE and cannot be used as an expression.")
            
    def declare_label(self, label, statement = None):
        """Declara uma label no scope atual."""
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

    def register_goto_label(self, label):
        """Regista um GOTO para validação no fim do scope."""
        label_key = f"__label_{label}"
        # Se o label já existe, verificar se é um label válido (is_label = True). Se não existir, guardar para verificar no fim do scope. 
        if label_key in self.__table:
            if not self.__table[label_key]['is_label']:
                raise SemanticError(f"GOTO or DO target '{label}' is not a label.")
        self.gotos_to_verify.append((self.get_current_scope_name(), label))

    def verify_pending_gotos(self, scope_filter=None):
        """Verifica GOTOs pendentes (existência de label e mesmo scope)."""
        errors = []
        save_table = self.__table # guardar a tabela atual para voltar a ela 
        
        for scope_name, label in self.gotos_to_verify:
            label_key = f"__label_{label}"
            scope_vars = self.__all_scopes[scope_name]['vars'] # mudar para a tabela do scope onde o GOTO foi declarado
            
            if label_key in scope_vars:
                if not scope_vars[label_key]['is_label']:
                    errors.append(f"GOTO target '{label}' in scope '{scope_name}' is not a label.")
                continue
            
            # verificar nos outros scopes
            found_another_scope = [
                scope_name for scope_name, scope_info in self.__all_scopes.items()
                if label_key in scope_info['vars'] and scope_info['vars'][label_key]['is_label']
            ]
            
            if found_another_scope:
                errors.append(f"GOTO target '{label}' in scope '{scope_name}' is not defined in this scope (found in scopes: {', '.join(found_another_scope)}).")
            else:
                errors.append(f"GOTO target label '{label}' in scope '{scope_name}' is not defined.")
                
            self.__table = save_table # voltar à tabela original
        
        if errors:
            raise SemanticError("\n".join(errors))
        
    def register_do_label(self, label):
        """Regista a label terminal de um DO para validação posterior."""
        self.do_labels_to_verify.append((self.get_current_scope_name(), label))

    def check_valid_do_label(self, label):
        """Valida que a label final de um DO não aponta para um statement inválido."""
        label_key = f"__label_{label}"
        label_info = self.__table[label_key]
        stmt_type = label_info.get('statement')[0]
        wrong_label = {'IF', 'DO', 'STOP', 'RETURN', 'PAUSE', 'END', 'ELSEIF', 'ELSE', 'ENDIF', 'THEN'}

        if stmt_type in wrong_label:
            raise SemanticError(f"Invalid terminal statement for DO label {label}: {stmt_type}.")
        
    def verify_pending_do_labels(self):
        """Verifica todas as labels de DO registadas no scope onde foram usadas."""
        errors = []
        current_table = self.__table # guardar a tabela atual para voltar a ela 

        for scope_name, label in self.do_labels_to_verify:
            self.__table = self.__all_scopes[scope_name]['vars'] # mudar para a tabela do scope onde o DO foi declarado
            try:
                self.check_valid_do_label(label)
            except SemanticError as e:
                errors.append(str(e))
        self.__table = current_table # voltar à tabela original
        
        if errors:
            raise SemanticError("\n".join(errors))

    def check_do_loop(self, var_name, start_type, end_type, step_type=None):
        """Valida tipos da variável/limites/passo num loop DO."""
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
        """Verifica no fim as chamadas guardadas."""
        errors = []
        original_scope_name = self.__scope_stack[-1]

        for node, scope_name in self.calls_to_verify:
            name = node[1] 
            args = node[2] 
            
            if scope_name in self.__all_scopes:
                self.__table = self.__all_scopes[scope_name]['vars']
            
            # verificar se a função existe 
            if name not in self.__all_scopes:
                errors.append(f"Undefined function/subroutine: '{name}'.")
                continue
    
            try:
                args_types = [self.get_expr_type(arg) for arg in args]
                
                # validar se é função/subrotina e se os argumentos estão corretos
                if node[0] == 'INDEX_OR_CALL':
                    self.check_is_function(name)
                elif node[0] == 'CALL':
                    self.check_is_subroutine(name)
                    
                self.check_call_args(name, args_types)
            except SemanticError as e:
                errors.append(str(e))
                
        # restaurar a tabela para o escopo original
        self.__table = self.__all_scopes[original_scope_name]['vars']
        if errors:
            raise SemanticError("\n".join(errors))
        
    def go_to_scope(self, scope_name):
        """Muda a tabela atual para a do escopo indicado ou GLOBAL."""
        if scope_name is None:
            scope_name = 'GLOBAL'
        if scope_name not in self.__all_scopes:
            raise SemanticError(f"Scope '{scope_name}' not found.")
        self.__current_scope = scope_name
        self.__table = self.__all_scopes[scope_name]['vars']
                
            
        
