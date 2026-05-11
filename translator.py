
import code

class Translator:
    def __init__(self, symbol_table):
        self.symbol_table = symbol_table        
        self.label_count = 0
        # self.functions_code = {} # para armazenar o código de cada função/subrotina
        self.current_scope = None # None - escopo global, ou nome da função/subrotina atual
        self.variables = {}
        self.next_addr = 0
        self.pending_do = {} # para armazenar informações de loops DO pendentes (variável, limite inferior, limite superior, passo)

    def translate(self, program_units):
        code = []
        
        #print("list: ")
        #print(code)
        for p in program_units:
            op = p[0]
            if op == 'PROGRAM':
                program_code = self.gen_program(p)
                code += program_code
            elif op == 'FUNCTION':
                func_code =  self.gen_function(p)
                code += func_code
            elif op == 'SUBROUTINE':
                subr_code = self.gen_subroutine(p)
                code += subr_code
            #print("list: ")
            #print(code)
        return code

    def translate_node(self, node):
        if isinstance(node, list):  # ← Adiciona isto
            code = []
            for stmt in node:
                result = self.translate_node(stmt)
                if result:
                    if isinstance(result, list):
                        code.extend(result)
                    else:
                        code.append(result)
            return code
        
        if not isinstance(node, tuple):
            return str(node)
        op = node[0]
        
        if op == 'DECLARE':                    # SORAIA
            return self.gen_declaration(node)
        elif op == 'ASSIGN':
            return self.gen_assign(node)
        elif op == 'IF':                         #  SOFIA
            return self.gen_if(node)
        elif op == 'DO':
            return self.gen_do(node)
        elif op == 'GOTO':
            return self.gen_goto(node)
        elif op == 'LABEL':                      # SORAIA
            return self.gen_label(node)
        elif op == 'CALL':                       #   SOFIA
            return self.gen_call(node)
        elif op == 'READ':
            return self.gen_read(node)
        elif op == 'STOP':                       # SORAIA
            return self.gen_stop(node)
        elif op == 'WRITE':                       #  SOFIA
            return self.gen_write(node)
        elif op == 'CONTINUE':
            return self.gen_continue(node)
        elif op == 'PRINT':
            return self.gen_print(node)
        elif op in ('ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'POWER'):
            return self.gen_arithmetic(node, op)
        elif op in ('LT', 'GT', 'LE', 'GE', 'EQ', 'NE'):        #   SOFIA
            return self.gen_relational(node)
        elif op in ('AND', 'OR'):                               #   SOFIA
            return self.gen_logical(node)
        elif op == 'NOT':
            return self.gen_not(node)
        elif op == 'CONCAT':                                    # SORAIA
            return self.gen_concat(node)
        elif op == 'PARAMETER':                                 #   SOFIA
            return self.gen_parameter(node)
        elif op == 'INDEX_OR_CALL':                             #   SOFIA
            return self.gen_index_or_call(node)

        return ["// Unhandled node: " + str(op)]

    def allocate_vars(self):
        code = []
        vars = self.symbol_table.get_table(self.current_scope)
        for name, value in vars.items():
            if value['is_parameter'] or value['is_label'] or value['is_return_value'] or value['is_formal_param']:
                continue # já inicializados
            
            if value['is_array']:
                size = value['size']
                code.append(f"PUSHN {size}") # para reservar as N posiçoes
            else:
                if value['type'] == 'INTEGER':
                    code.append("PUSHI 0")
                elif value['type'] == 'REAL':
                    code.append("PUSHF 0.0")
                elif value['type'] == 'LOGICAL':
                    code.append("PUSHI 0")
                elif value['type'] == 'CHARACTER':
                    code.append("PUSHS \"\"")
                elif value['type'] == 'DOUBLE':
                    code.append("PUSHF 0.0")

        return code


    def gen_program(self, node):
        _, name, body = node
        self.current_scope = name
        code = []
        self.symbol_table.go_to_scope(name) # entrar no escopo do programa
        code += self.allocate_vars()
        code += self.translate_node(body)
        self.symbol_table.go_to_scope(None) # voltar para escopo global
        code.append("STOP") # para não executar codigo das funções/subrotinas
        code.append("\n")
        return code
    
    def gen_function(self, node):
        _, type, name, params, body = node
        self.current_scope = name

        code = []
        func_label = f"FUNC{name}"
        code.append(func_label + ":")

        count = -1
        for p in params: # push dos params
            code.append(f"PUSHL {count}")
            count -= 1
        
        self.symbol_table.go_to_scope(name) # entrar no escopo da função
        code += self.allocate_vars() # alocar espaço para variáveis locais

        code += self.translate_node(body)
        code.append("RETURN")
        code.append("\n")
        self.symbol_table.go_to_scope(None)

        return
    
    def gen_subroutine(self, node):
        _, name, params, body = node
        self.current_scope = name

        code = []
        func_label = f"SUBROUTINE{name}"
        code.append(func_label + ":")

        count = -1
        for p in params: # push dos params
            code.append(f"PUSHL {count}")
            count -= 1
        
        self.symbol_table.go_to_scope(name) # entrar no escopo da subrotina
        code += self.allocate_vars() # alocar espaço para variáveis locais

        code += self.translate_node(body)

        self.symbol_table.go_to_scope(None)
        code.append("RETURN")
        code.append("\n")

        return
    
    def gen_declaration(self, node): 
        # allocs de todas as vars declaradas são feitas no inicio da program unit
        return None


    def gen_assign(self, node):
        _, var, expr = node
        # Se expr for um tuplo, traduzimos primeiro a expressão
        pos_var = self.symbol_table.get_index(var)
        code = []
        if isinstance(expr, tuple):
            code = self.translate_node(expr)
        else:
            type = self.symbol_table.get_type(var)
            if type == 'INTEGER':
                code.append(f"PUSHI {expr}")
            elif type == 'REAL':
                code.append(f"PUSHF {expr}")
            elif type == 'LOGICAL':
                value = 0
                if expr is True:
                    value = 1
                code.append(f"PUSHI {value}")
            elif type == 'CHARACTER':
                code.append(f"PUSHS \"{expr}\"")
            elif type == 'DOUBLE':
                code.append(f"PUSHF {expr}")

        if isinstance(var, tuple) and var[0] == 'INDEX_OR_CALL': # caso seja um acesso a array, tipo NUMS(I)
            _, var_name, index_expr = var
            # 1.1. Colocar o endereço base da struct na pilha
            # Usamos PUSHG ou PUSHL dependendo de onde o ponteiro da struct está guardado
            pos_var = self.symbol_table.get_index(var_name)
            if self.symbol_table.is_global(var_name):
                code.append(f"PUSHG {pos_var}")
            else:
                code.append(f"PUSHL {pos_var}")

            # 1.2. Calcular o índice (I - 1)
            code
            code.append("PUSHI 1")
            code.append("SUB") # Topo agora tem o offset (I-1)

            # 1.3. Calcular o valor da expressão a ser guardada
            code.extend(self.translate_node(expr))

            # 1.4. Usar STOREN (v, n, a -> a[n] = v)
            # A pilha está: [EndereçoBase, Offset, Valor]
            # Mas STOREN espera: Valor, Offset, Endereço. Precisamos ajustar.
            # Se a tua VM segue v, n, a:
            code.append("SWAP")      # [Endereço, Valor, Offset]
            code.append("COPY 3")    # [Endereço, Valor, Offset, Endereço] - copia base para o fim
            code.append("STOREN")    # Executa a[n] = v
            # Nota: Dependendo da ordem exata de POP do teu STOREN, 
            # podes precisar de mais SWAPs para alinhar [Valor, Offset, Endereço].
            return code

        if self.symbol_table.is_return_value(var):
            address = self.symbol_table.get_return_address(var)
            code.append(f"STOREL {address}")
        elif self.symbol_table.get_current_scope_type() == 'FUNCTION' or self.symbol_table.get_current_scope_type() =='SUBROUTINE':
            code.append(f"STOREL {pos_var}")
        else:    
            code.append(f"STOREG {pos_var}")
            
        return code
    
            
        
# PRINT *, 'BASE ', BASE, ': ', RESULT
# PRINT *, 'INTRODUZA UM NUMERO DECIMAL INTEIRO:'
# PRINT *, 'A soma dos numeros e: ', SOMA
    def gen_print(self, node):
        _, ast, args = node
        code = []
        if not args: # PRINT * sem argumentos ->imprime lista vazia
            code.append('PUSHS')
            code.append("WRITES")
            return code
        
        for arg in args:
            if isinstance(arg, bool): # PRINT * BOOL
                if arg:
                    code.append('PUSHS ".TRUE."')
                else:
                    code.append('PUSHS ".FALSE."')
                code.append("WRITES")
            elif isinstance(arg, int): # PRINT * INTEGER
                code.append(f"PUSHI {arg}")
                code.append("WRITEI")
            elif isinstance(arg, float): # PRINT * REAL/DOUBLE
                code.append(f"PUSHF {arg}")
                code.append("WRITEF")
            elif isinstance(arg, str): # PRINT * STRING
                try:
                    idx = self.symbol_table.get_index(arg)
                    var_type = self.symbol_table.get_type(arg)
                    code.append(f"PUSHG {idx}")

                    if var_type in ("REAL", "DOUBLE"):
                        code.append("WRITEF")
                    elif var_type == "CHARACTER":
                        code.append("WRITES")
                    else: # INTEGER, BOOL
                        code.append("WRITEI")
                except Exception:
                    arg = arg[1:-1] # porque vem com aspas do parser
                    # Se nao existir na symbol table, tratamos como string literal
                    arg = arg.replace('"', '\\"') # Escapar aspas
                    code.append(f'PUSHS "{arg}"')
                    code.append("WRITES")

        return code


    def gen_arithmetic(self, node, instr):
        _, left, right = node
        code = []
        # esquerda
        if isinstance(left, tuple):
            left_code = self.translate_node(left)
            if left_code:
                code.extend(left_code.splitlines())
        elif isinstance(left, bool):
            code.append(f"PUSHI {1 if left else 0}")
        elif isinstance(left, int):
            code.append(f"PUSHI {left}")
        elif isinstance(left, float):
            code.append(f"PUSHF {left}")
        elif isinstance(left, str):
            idx = self.symbol_table.get_index(left)
            code.append(f"PUSHG {idx}")

        # direita
        if isinstance(right, tuple):
            right_code = self.translate_node(right)
            if right_code:
                code.extend(right_code.splitlines())
        elif isinstance(right, bool):
            code.append(f"PUSHI {1 if right else 0}")
        elif isinstance(right, int):
            code.append(f"PUSHI {right}")
        elif isinstance(right, float):
            code.append(f"PUSHF {right}")
        elif isinstance(right, str):
            idx = self.symbol_table.get_index(right)
            code.append(f"PUSHG {idx}")

        # operação
        op_map = {
            'ADD': 'ADD',
            'SUB': 'SUB',
            'MUL': 'MUL',
            'DIV': 'DIV',
            'MOD': 'MOD',
            'POWER': 'POW'
        }
        code.append(op_map[instr])
        return code
    
    def gen_not(self, node):
        _, expr = node
        code = []

        if isinstance(expr, tuple): # 
            expr_code = self.translate_node(expr)
            if expr_code:
                code.extend(expr_code.splitlines())
        elif isinstance(expr, bool):
            code.append(f"PUSHI {1 if expr else 0}")
        elif isinstance(expr, int):
            code.append(f"PUSHI {expr}")
        elif isinstance(expr, str):
            idx = self.symbol_table.get_index(expr)
            code.append(f"PUSHG {idx}")

        code.append("PUSHI 0")
        code.append("EQUAL")

        return code
    
    def gen_read(self, node): # NAO PERCEBI ESTA
        _, ast, args = node
        code = []
        for arg in args:
            if isinstance(arg, str):
                idx = self.symbol_table.get_index(arg)
                var_type = self.symbol_table.get_type(arg)
                code.append("READ")

                if var_type == "INTEGER" or var_type == "LOGICAL":
                    code.append("ATOI")
                    code.append(f"STOREG {idx}")
                elif var_type in ("REAL", "DOUBLE"):
                    code.append("ATOF")
                    code.append(f"STOREG {idx}")
                else: # CHARACTER
                    code.append(f"STOREG {idx}")
            
            elif isinstance(arg, tuple) and arg[0] == 'INDEX_OR_CALL':  # ('INDEX_OR_CALL', 'NUMS', ['I']) | READ *, NUMS(I)
                _, name, indices = arg
                
                if len(indices) == 1:

                    idx = self.symbol_table.get_index(name)
                    array_type = self.symbol_table.get_type(name)
                    index_expr = indices[0]
                    code.append(f"PUSHG {idx}") # base address do array

                    # Em Fortran os arrays começam em 1, mas na heap vamos usar índice 0, entao NUMS(I) vira endereço NUMS + (I - 1).
                    if isinstance(index_expr, tuple):
                        index_code = self.translate_node(index_expr)
                        if index_code:
                            code.extend(index_code.splitlines())
                    elif isinstance(index_expr, int):
                        code.append(f"PUSHI {index_expr}")
                    elif isinstance(index_expr, str):
                        idx_index = self.symbol_table.get_index(index_expr)
                        code.append(f"PUSHG {idx_index}")
                    
                    # Converter índice Fortran 1-based para índice 0-based
                    code.append("PUSHI 1")
                    code.append("SUB")

                    code.append("READ") # ler o valor

                    if array_type in ("INTEGER", "LOGICAL"):
                        code.append("ATOI")
                    elif array_type in ("REAL", "DOUBLE"):
                        code.append("ATOF")

                    code.append("STOREN") # armazenar na heap. array[index] = valor

        return code

    def gen_do(self, node): # NAO PERCEBI BEM ESTA
        _, target_label, var, start, end, step = node
        code = []

        # gerar labels únicos para o início e fim do loop
        self.label_count += 1
        loop_id = self.label_count

        start_label = f"DO{target_label}{loop_id}START"
        end_label = f"DO{target_label}{loop_id}END"

        # inx da variável de controlo do loop
        var_idx = self.symbol_table.get_index(var)

        # inicializar a var do loop
        if isinstance(start, tuple):
            start_code = self.translate_node(start)
            if start_code:
                code.extend(start_code.splitlines())
        elif isinstance(start, int):
            code.append(f"PUSHI {start}")
        elif isinstance(start, float):
            code.append(f"PUSHF {start}")
        elif isinstance(start, str):
            idx = self.symbol_table.get_index(start)
            code.append(f"PUSHG {idx}")

        code.append(f"STOREG {var_idx}")

        # label de inicio do loop
        code.append(f"{start_label}:")

        # condiçao do loop
        code.append(f"PUSHG {var_idx}") # valor atual da variável de controlo
        if isinstance(end, tuple):
            end_code = self.translate_node(end)
            if end_code:
                code.extend(end_code.splitlines())
        elif isinstance(end, int):
            code.append(f"PUSHI {end}")
        elif isinstance(end, float):
            code.append(f"PUSHF {end}")
        elif isinstance(end, str):
            idx = self.symbol_table.get_index(end)
            code.append(f"PUSHG {idx}")

        code.append("INFEQ") # condição de saída: var > end

        code.append(f"JZ {end_label}") # se var > end, saltar para o fim do loop

        # guardar info para fechar o loop no CONTINUE
        self.pending_do[target_label] = {
            "var": var,
            "var_idx": var_idx,
            "step": step,
            "start_label": start_label,
            "end_label": end_label
        }
        return code
    
    def gen_continue(self, node): # acho que é assim por causa do DO
        pass

    def gen_goto(self, node):
        _, label = node
        return f"JUMP LABEL{label}"
       
    def gen_if(self, node):
        _, cond, then_body, else_body = node
        code = []

        self.label_count += 1
        if_id = self.label_count
        else_label = f"IF{if_id}ELSE"
        end_label  = f"IF{if_id}END"

        if isinstance(cond, tuple):
            code.extend(self.translate_node(cond).splitlines())
        elif isinstance(cond, bool):
            code.append(f"PUSHI {1 if cond else 0}")
        elif isinstance(cond, int):
            code.append(f"PUSHI {cond}")
        elif isinstance(cond, str):
            idx = self.symbol_table.get_index(cond)
            code.append(f"PUSHG {idx}")

        code.append(f"JZ {else_label if else_body else end_label}")

        then_code = self.translate_node(then_body)
        if then_code:
            code.extend(then_code.splitlines())

        if else_body:
            code.append(f"JUMP {end_label}")
            code.append(f"{else_label}:")
            else_code = self.translate_node(else_body)
            if else_code:
                code.extend(else_code.splitlines())

        code.append(f"{end_label}:")
        return code

    
    def gen_call(self, node):
        _, name, args = node
        code = []

        for arg in args:
            if isinstance(arg, tuple):
                code.extend(self.translate_node(arg).splitlines())
            elif isinstance(arg, bool):
                code.append(f"PUSHI {1 if arg else 0}")
            elif isinstance(arg, int):
                code.append(f"PUSHI {arg}")
            elif isinstance(arg, float):
                code.append(f"PUSHF {arg}")
            elif isinstance(arg, str):
                if arg.startswith("'") and arg.endswith("'"):
                    literal = arg[1:-1].replace('"', '\\"')
                    code.append(f'PUSHS "{literal}"')
                else:
                    idx = self.symbol_table.get_index(arg)
                    code.append(f"PUSHG {idx}")

        code.append(f"PUSHA SUBROUTINE_{name}")
        code.append("CALL")
        return code

    
    def gen_write(self, node):
        _, control_spec, args = node
        code = []

        for arg in args:
            if isinstance(arg, bool):
                code.append('PUSHS ".TRUE."' if arg else 'PUSHS ".FALSE."')
                code.append("WRITES")
            elif isinstance(arg, int):
                code.append(f"PUSHI {arg}")
                code.append("WRITEI")
            elif isinstance(arg, float):
                code.append(f"PUSHF {arg}")
                code.append("WRITEF")
            elif isinstance(arg, tuple):
                code.extend(self.translate_node(arg).splitlines())
                arg_type = self.symbol_table.get_expr_type(arg)
                if arg_type in ("REAL", "DOUBLE"):
                    code.append("WRITEF")
                elif arg_type == "CHARACTER":
                    code.append("WRITES")
                else:
                    code.append("WRITEI")
            elif isinstance(arg, str):
                if arg.startswith("'") and arg.endswith("'"):
                    literal = arg[1:-1].replace('"', '\\"')
                    code.append(f'PUSHS "{literal}"')
                    code.append("WRITES")
                else:
                    idx = self.symbol_table.get_index(arg)
                    var_type = self.symbol_table.get_type(arg)
                    code.append(f"PUSHG {idx}")
                    if var_type in ("REAL", "DOUBLE"):
                        code.append("WRITEF")
                    elif var_type == "CHARACTER":
                        code.append("WRITES")
                    else:
                        code.append("WRITEI")

        code.append('PUSHS "\\n"')
        code.append("WRITES")
        return code

    
    def gen_relational(self, node):
        op, left, right = node
        code = []

        if isinstance(left, tuple):
            code.extend(self.translate_node(left).splitlines())
        elif isinstance(left, bool):
            code.append(f"PUSHI {1 if left else 0}")
        elif isinstance(left, int):
            code.append(f"PUSHI {left}")
        elif isinstance(left, float):
            code.append(f"PUSHF {left}")
        elif isinstance(left, str):
            if left.startswith("'") and left.endswith("'"):
                literal = left[1:-1].replace('"', '\\"')
                code.append(f'PUSHS "{literal}"')
            else:
                idx = self.symbol_table.get_index(left)
                code.append(f"PUSHG {idx}")

        if isinstance(right, tuple):
            code.extend(self.translate_node(right).splitlines())
        elif isinstance(right, bool):
            code.append(f"PUSHI {1 if right else 0}")
        elif isinstance(right, int):
            code.append(f"PUSHI {right}")
        elif isinstance(right, float):
            code.append(f"PUSHF {right}")
        elif isinstance(right, str):
            if right.startswith("'") and right.endswith("'"):
                literal = right[1:-1].replace('"', '\\"')
                code.append(f'PUSHS "{literal}"')
            else:
                idx = self.symbol_table.get_index(right)
                code.append(f"PUSHG {idx}")

        op_map = {
            'LT': 'INF',
            'LE': 'INFEQ',
            'GT': 'SUP',
            'GE': 'SUPEQ',
            'EQ': 'EQUAL',
        }
        if op == 'NE':
            code.append("EQUAL")
            code.append("PUSHI 0")
            code.append("EQUAL")
        else:
            code.append(op_map[op])

        return code
    
    def gen_logical(self, node):
        op, left, right = node
        code = []

        if isinstance(left, tuple):
            code.extend(self.translate_node(left).splitlines())
        elif isinstance(left, bool):
            code.append(f"PUSHI {1 if left else 0}")
        elif isinstance(left, str):
            idx = self.symbol_table.get_index(left)
            code.append(f"PUSHG {idx}")

        if isinstance(right, tuple):
            code.extend(self.translate_node(right).splitlines())
        elif isinstance(right, bool):
            code.append(f"PUSHI {1 if right else 0}")
        elif isinstance(right, str):
            idx = self.symbol_table.get_index(right)
            code.append(f"PUSHG {idx}")

        if op == 'AND':
            code.append("MUL")
        else:  # OR
            code.append("ADD")
            code.append("PUSHI 0")
            code.append("GT")

        return code
    
    def gen_parameter(self, node):
        # _, params = node
        # code = []

        # # PARAMETER declara constantes em Fortran.
        # # O parser já as registou na symbol table com is_parameter=True e value=valor.
        # # Aqui geramos código para inicializar essas posições de memória em runtime,
        # # porque a VM não tem conceito de constantes — são apenas variáveis que não mudam.
        # for var, value in params:
        #     idx = self.symbol_table.get_index(var)  # posição global da constante

        #     if isinstance(value, bool):
        #         code.append(f"PUSHI {1 if value else 0}")
        #     elif isinstance(value, int):
        #         code.append(f"PUSHI {value}")
        #     elif isinstance(value, float):
        #         code.append(f"PUSHF {value}")
        #     elif isinstance(value, str):
        #         code.append(f'PUSHS "{value}"')
        #     elif isinstance(value, tuple):
        #         val_code = self.translate_node(value)
        #         if val_code:
        #             code.extend(val_code.splitlines())

        #     code.append(f"STOREG {idx}")

        # return "\n".join(code)
        return "" # como as constantes já estão na symbol table, não precisamos de gerar código para elas. Se gerássemos, estariamos a sobrescrever o valor delas, o que não faz sentido.

    
    def gen_index_or_call(self, node):
        _, name, args = node
        code = []

        if self.symbol_table.is_array(name):
            idx = self.symbol_table.get_index(name)
            code.append(f"PUSHG {idx}")

            index_expr = args[0]
            if isinstance(index_expr, tuple):
                code.extend(self.translate_node(index_expr).splitlines())
            elif isinstance(index_expr, int):
                code.append(f"PUSHI {index_expr}")
            elif isinstance(index_expr, str):
                idx_i = self.symbol_table.get_index(index_expr)
                code.append(f"PUSHG {idx_i}")

            code.append("PUSHI 1")
            code.append("SUB")
            code.append("LOADN")

        else:
            for arg in args:
                if isinstance(arg, tuple):
                    code.extend(self.translate_node(arg).splitlines())
                elif isinstance(arg, bool):
                    code.append(f"PUSHI {1 if arg else 0}")
                elif isinstance(arg, int):
                    code.append(f"PUSHI {arg}")
                elif isinstance(arg, float):
                    code.append(f"PUSHF {arg}")
                elif isinstance(arg, str):
                    if arg.startswith("'") and arg.endswith("'"):
                        literal = arg[1:-1].replace('"', '\\"')
                        code.append(f'PUSHS "{literal}"')
                    else:
                        idx = self.symbol_table.get_index(arg)
                        code.append(f"PUSHG {idx}")

            code.append(f"PUSHA FUNC_{name}")
            code.append("CALL")

        return code
    


    # label, stop, concat, declare
    def gen_label(self, node):
        _, label_name, statement = node
        scope_name = self.symbol_table.get_current_scope_name()
        full_label_name = f"{scope_name}{label_name}"
        code = [full_label_name + ":"] 
        code += self.translate_node(statement)
        return code
    
    def gen_stop(self, node):
        _, arg_type, arg_value = node
        code = []

        if arg_type:
            if arg_type == 'INT':
                code.append(f"PUSHI {arg_value}")
                code.append("WRITEI")
            elif arg_type == 'STRING':
                code.append(f"PUSHS \"{arg_value}\"")
                code.append("WRITES")
            code.append("WRITELN")
        
        code.append("STOP")
        return code
    
    def gen_concat(self, node):
        _, left, right = node
        code = []
        code.append(self.translate_node(left))
        code.append(self.translate_node(right))
        code.append("CONCAT")
        return code
    
    def gen_write(self, node):
        _, control_spec, args = node
        code = []

        # WRITE(*,*) sem argumentos -> linha vazia
        if not args:
            code.append('PUSHS "\\n"')
            code.append("WRITES")
            return code

        for arg in args:
            if isinstance(arg, bool):
                if arg:
                    code.append('PUSHS ".TRUE."')
                else:
                    code.append('PUSHS ".FALSE."')
                code.append("WRITES")

            elif isinstance(arg, int):
                code.append(f"PUSHI {arg}")
                code.append("WRITEI")

            elif isinstance(arg, float):
                code.append(f"PUSHF {arg}")
                code.append("WRITEF")

            elif isinstance(arg, str):
                try:
                    # Se existir na symbol table, é variável
                    idx = self.symbol_table.get_index(arg)
                    var_type = self.symbol_table.get_type(arg)

                    code.append(f"PUSHG {idx}")

                    if var_type in ("REAL", "DOUBLE"):
                        code.append("WRITEF")
                    elif var_type == "CHARACTER":
                        code.append("WRITES")
                    elif var_type == "LOGICAL":
                        # Simples: escreve 0/1, tal como tens noutros pontos
                        code.append("WRITEI")
                    else:
                        code.append("WRITEI")

                except Exception:
                    # Se não existir na symbol table, é string literal vinda do parser
                    # Exemplo: "'IGUAL'" -> "IGUAL"
                    if len(arg) >= 2 and arg[0] == "'" and arg[-1] == "'":
                        arg = arg[1:-1]

                    arg = arg.replace('"', '\\"')
                    code.append(f'PUSHS "{arg}"')
                    code.append("WRITES")

            elif isinstance(arg, tuple):
                arg_code = self.translate_node(arg)
                if arg_code:
                    code.extend(arg_code.splitlines())

                expr_type = self.symbol_table.get_expr_type(arg)

                if expr_type in ("REAL", "DOUBLE"):
                    code.append("WRITEF")
                elif expr_type in ("CHARACTER", "STRING"):
                    code.append("WRITES")
                else:
                    code.append("WRITEI")

        return code