
import code


class Translator:
    def __init__(self, symbol_table):
        self.symbol_table = symbol_table        
        self.label_count = 0
        self.functions_code = {} # para armazenar o código de cada função/subrotina
        self.current_scope = None # None - escopo global, ou nome da função/subrotina atual
        self.variables = {}
        self.next_addr = 0
        self.pending_do = {} # para armazenar informações de loops DO pendentes (variável, limite inferior, limite superior, passo)

    def translate(self, node):
        if isinstance(node, list):
            return "\n".join([self.translate(n) for n in node])
        
        if not isinstance(node, tuple): #erro
            return str(node) # Caso seja um valor atómico (INT, VAR)

        op = node[0]
        
        # Despacho manual (ou podes usar getattr para algo mais dinâmico)
        if op == 'PROGRAM':
            return self.gen_program(node)
        elif op == 'FUNCTION':                   # SORAIA
            return self.gen_function(node)
        elif op == 'SUBROUTINE':                 # SORAIA
            return self.gen_subroutine(node)
        elif op == 'DECLARE':                    # SORAIA
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
        elif op in ('ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'POW'):
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

        return f"; Unknown node {op}"

    def gen_program(self, node):
        _, name, body = node
        code = []
        code.append(self.translate(body))
        return code
    
    def gen_function(self, node):
        _, type, indexorcall, body = node
        name, args = indexorcall

        code = []
        func_label = f"FUNC_{name}"
        code.append(f"{func_label}:")

        count = -1
        for a in args:
            code.append(f"PUSHL {count}")
            count -= 1

        code.append(self.translate(body))
        self.functions_code[name] = code
        return
    
    def gen_subroutine(self, node):
        _, name, args, body = node

        code = []
        func_label = f"FUNC_{name}"
        code.append(f"{func_label}:")
        code.append(self.translate(body))
        self.functions_code[name] = code
        return
    
    def gen_declaration(self, node): # ('DECLARE', 'INTEGER', [('A', 'INTEGER'), ('B', 'INTEGER')])
        _, type,  vars_declared = node
        code = []
        for var in vars_declared:
            name = var[0]
            
            idx = self.symbol_table.get_index(name)
            # se for array - ('NUMS', 'INTEGER', 5)
            if self.symbol_table.is_array(name):
                size = var[2]

            # se for variavel normal - ('A', 'INTEGER')
            else:
                return

            # if name not in self.variables:
            #     self.variables[name] = self.next_addr
            #     self.next_addr += size


    def gen_assign(self, node):
        _, var, expr = node
        # Se expr for um tuplo, traduzimos primeiro a expressão
        pos_var = self.symbol_table.get_index(var)
        if isinstance(expr, tuple):
            code = self.translate(expr)
        else:
            if self.symbol_table.is_array(var):
                pass #idk
            else:
                type = self.symbol_table.get_type(var)
                if type == 'INTEGER':
                    code.append(f"PUSHI {expr}")
                elif type == 'REAL':
                    code.append(f"PUSHF {expr}")
                elif type == 'BOOL':
                    value = 0
                    if expr is True:
                        value = 1
                    code.append(f"PUSHI {value}")
                elif type == 'CHARACTER':
                    code.append(f"PUSHS \"{expr}\"")
                elif type == 'DOUBLE':
                    code.append(f"PUSHF {expr}")
            
            code.append(f"STOREG {pos_var}")
            
        return code
        
    def gen_print(self, node):
        _, ast, args = node
        code = []
        if not args: # PRINT * sem argumentos ->imprime lista vazia
            code.append('PUSHS "\\n"')
            code.append("WRITES")
            return "\n".join(code)
        
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
                    # Se nao existir na symbol table, tratamos como string literal
                    arg = arg.replace('"', '\\"') # Escapar aspas
                    code.append(f'PUSHS "{arg}"')
                    code.append("WRITES")

        code.append('PUSHS "\\n"')
        code.append("WRITES")
        return "\n".join(code)


    def gen_arithmetic(self, node, instr):
        _, left, right = node
        code = []
        # esquerda
        if isinstance(left, tuple):
            left_code = self.translate(left)
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
            right_code = self.translate(right)
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
            'POW': 'POW'
        }
        code.append(op_map[instr])
        return "\n".join(code)
    
    def gen_not(self, node):
        _, expr = node
        code = []

        if isinstance(expr, tuple): # 
            expr_code = self.translate(expr)
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

        return "\n".join(code)
    
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
                        index_code = self.translate(index_expr)
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

        return "\n".join(code)

    def gen_do(self, node): # NAO PERCEBI BEM ESTA
        _, target_label, var, start, end, step = node
        code = []

        # gerar labels únicos para o início e fim do loop
        self.label_count += 1
        loop_id = self.label_count

        start_label = f"DO_{target_label}_{loop_id}_START"
        end_label = f"DO_{target_label}_{loop_id}_END"

        # inx da variável de controlo do loop
        var_idx = self.symbol_table.get_index(var)

        # inicializar a var do loop
        if isinstance(start, tuple):
            start_code = self.translate(start)
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
            end_code = self.translate(end)
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
        return "\n".join(code)
    
    def gen_continue(self, node): # acho que é assim por causa do DO
        return "" 

    def gen_goto(self, node):
        _, label = node
        return f"JUMP LABEL_{label}"