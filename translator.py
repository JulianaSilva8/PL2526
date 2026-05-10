
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

    def translate(self, node):
        if isinstance(node, list):
            results = []
            for n in node:
                result = self.translate(n)
                if result:  # Ignorar None e strings vazias
                    results.append(result)
            return "\n".join(results) if results else ""
        
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
        vars = self.symbol_table.get_table()
        for name, value in vars.items():
            if value['is_parameter'] or value['is_label']:
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
        code = []
        self.symbol_table.push_scope() # scope do programa
        code.append(self.allocate_vars()) # alocar espaço para variáveis globais
        code.append(self.translate(body))
        self.symbol_table.pop_scope(name) # idealmente o nome já estaria preenchido na analise semantica

        code.append("STOP") # para não executar codigo das funções/subrotinas
        return code
    
    def gen_function(self, node):
        _, type, indexorcall, body = node
        name, args = indexorcall

        code = []
        func_label = f"FUNC_{name}"
        code.append(func_label + ":")

        count = -1
        for a in args: # push dos params
            code.append(f"PUSHL {count}")
            count -= 1
        
        self.symbol_table.push_scope() # scope da função
        code.append(self.allocate_vars()) # alocar espaço para variáveis locais

        code.append(self.translate(body))
        code.append("RETURN")
        
        self.symbol_table.pop_scope(name, type) # idealmente o nome e o tipo já estariam preenchidos na analise semantica
        return
    
    def gen_subroutine(self, node):
        _, name, args, body = node

        code = []
        func_label = f"SUBROUTINE_{name}"
        code.append(func_label + ":")

        count = -1
        for a in args: # push dos params
            code.append(f"PUSHL {count}")
            count -= 1
        
        self.symbol_table.push_scope() # scope da função
        code.append(self.allocate_vars()) # alocar espaço para variáveis locais

        code.append(self.translate(body))

        self.symbol_table.pop_scope(name) # idealmente o nome já estaria preenchido na analise semantica
        code.append("RETURN")

        return
    
    def gen_declaration(self, node): 
        # allocs de todas as vars declaradas são feitas no inicio da program unit
        return None


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
                elif type == 'LOGICAL':
                    value = 0
                    if expr is True:
                        value = 1
                    code.append(f"PUSHI {value}")
                elif type == 'CHARACTER':
                    code.append(f"PUSHS \"{expr}\"")
                elif type == 'DOUBLE':
                    code.append(f"PUSHF {expr}")

        if self.symbol_table.is_array(var):
            pass #idk

        if self.symbol_table.is_return_value(var):
            address = self.symbol_table.get_return_address(var)
            code.append(f"STOREL {address}")
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
                    arg = arg[1:-1] # porque vem com aspas do parser
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
            'POWER': 'POW'
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
       
    def gen_if(self, node):
        _, condition, then_body, else_body = node
        code = []
        
        # Gerar labels únicos para os ramos
        self.label_count += 1
        else_label = f"ELSE_{self.label_count}"
        end_label = f"ENDIF_{self.label_count}"
        
        # Traduzir a condição
        if isinstance(condition, tuple):
            cond_code = self.translate(condition)
            if cond_code:
                code.extend(cond_code.splitlines() if isinstance(cond_code, str) else cond_code)
        elif isinstance(condition, bool):
            code.append(f"PUSHI {1 if condition else 0}")
        elif isinstance(condition, int):
            code.append(f"PUSHI {condition}")
        elif isinstance(condition, float):
            code.append(f"PUSHF {condition}")
        elif isinstance(condition, str):
            idx = self.symbol_table.get_index(condition)
            code.append(f"PUSHG {idx}")
            
        # Se condição falsa, pular para else (ou fim se não houver else)
        if else_body:
            code.append(f"JUMP {end_label}")
            code.append(f"{else_label}:")
            else_code = self.translate(else_body)
            if else_code:
                code.extend(else_code.splitlines())
        
        code.append(f"{end_label}:")
        return "\n".join(code)
    
    def gen_call(self, node): # NAO PERCEBI ESTA
        _, name, args = node
        code = []

        # Em Fortran, subrotinas recebem argumentos por referência.
        # Para cada argumento, calculamos o seu endereço absoluto
        # com PUSHGP (base do frame global) + PUSHI idx + PADD (soma de endereço).
        # A subrotina depois usa LOAD 0 / STORE 0 para ler/escrever pelo endereço.
        for arg in args:
            if isinstance(arg, str):
                # Variável simples: calcular endereço gp + idx
                idx = self.symbol_table.get_index(arg)
                code.append("PUSHGP")        # empurrar base do frame global
                code.append(f"PUSHI {idx}")  # empurrar o offset da variável
                code.append("PADD")          # endereço final = base + offset

            elif isinstance(arg, tuple) and arg[0] == 'INDEX_OR_CALL':
                # Elemento de array: NUMS(I) -> endereço = base_array + (I - 1)
                _, arr_name, indices = arg
                arr_idx = self.symbol_table.get_index(arr_name)
                code.append("PUSHGP")           # base do frame global
                code.append(f"PUSHI {arr_idx}") # offset do array
                code.append("PADD")             # endereço base do array
                # Calcular o índice (Fortran é 1-based, converter para 0-based)
                index_expr = indices[0] if indices else 0
                if isinstance(index_expr, tuple):
                    index_code = self.translate(index_expr)
                    if index_code:
                        code.extend(index_code.splitlines())
                elif isinstance(index_expr, int):
                    code.append(f"PUSHI {index_expr}")
                elif isinstance(index_expr, str):
                    idx_i = self.symbol_table.get_index(index_expr)
                    code.append(f"PUSHG {idx_i}")
                code.append("PUSHI 1")  # ajuste 1-based -> 0-based
                code.append("SUB")
                code.append("PADD")     # endereço final do elemento

            elif isinstance(arg, int):
                code.append(f"PUSHI {arg}")
            elif isinstance(arg, float):
                code.append(f"PUSHF {arg}")
            elif isinstance(arg, tuple):
                # Expressão calculada: traduzir normalmente
                arg_code = self.translate(arg)
                if arg_code:
                    code.extend(arg_code.splitlines())

        # Empurrar o endereço da label da subrotina e chamar
        code.append(f"PUSHA FUNC_{name}") # PUSHA: push do endereço da função/subrotina
        code.append("CALL")
        return "\n".join(code)
    
    def gen_write(self, node):
        # WRITE ainda não está totalmente no parser (control_spec ignorado por agora)
        # Comportamento igual ao gen_print
        _, control_spec, args = node
        code = []

        # Sem argumentos: imprimir linha vazia
        if not args:
            code.append("WRITELN")
            return "\n".join(code)

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
            elif isinstance(arg, str):
                try:
                    # Tentar encontrar na symbol table — é uma variável
                    idx = self.symbol_table.get_index(arg)
                    var_type = self.symbol_table.get_type(arg)
                    code.append(f"PUSHG {idx}")  # buscar valor da variável
                    # Escolher a instrução de escrita conforme o tipo
                    if var_type in ("REAL", "DOUBLE"):
                        code.append("WRITEF")
                    elif var_type == "CHARACTER":
                        code.append("WRITES")
                    else:  # INTEGER, LOGICAL
                        code.append("WRITEI")
                except Exception:
                    # Não está na symbol table — é uma string literal
                    arg = arg.replace('"', '\\"')  # escapar aspas internas
                    code.append(f'PUSHS "{arg}"')
                    code.append("WRITES")
            elif isinstance(arg, tuple):
                arg_code = self.translate(arg)
                if arg_code:
                    code.extend(arg_code.splitlines())
                code.append("WRITEI")

        code.append("WRITELN")
        return "\n".join(code)

    
    def gen_relational(self, node):
        op, left, right = node
        code = []

        # --- Traduzir lado esquerdo ---
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

        # --- Traduzir lado direito ---
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

        # --- Aplicar operador relacional ---
        if op == 'LT':
            code.append("INF")       # m < n
        elif op == 'GT':
            code.append("SUP")       # m > n
        elif op == 'LE':
            code.append("INFEQ")     # m <= n
        elif op == 'GE':
            code.append("SUPEQ")     # m >= n
        elif op == 'EQ':
            code.append("EQUAL")     # m == n
        elif op == 'NE': # m != n é equivalente a !(m == n)
            code.append("EQUAL")     # m == n ...
            code.append("NOT")       # ... negado -> m != n

        return "\n".join(code)
    
    def gen_logical(self, node):
        op, left, right = node
        code = []

        # --- Traduzir lado esquerdo ---
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

        # --- Traduzir lado direito ---
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

        # --- Aplicar operador lógico ---
        if op == 'AND':
            code.append("AND")
        elif op == 'OR':
            code.append("OR")

        return "\n".join(code)
    
    def gen_parameter(self, node):
        _, params = node
        code = []

        # PARAMETER declara constantes em Fortran.
        # O parser já as registou na symbol table com is_parameter=True e value=valor.
        # Aqui geramos código para inicializar essas posições de memória em runtime,
        # porque a VM não tem conceito de constantes — são apenas variáveis que não mudam.
        for var, value in params:
            idx = self.symbol_table.get_index(var)  # posição global da constante

            if isinstance(value, bool):
                code.append(f"PUSHI {1 if value else 0}")
            elif isinstance(value, int):
                code.append(f"PUSHI {value}")
            elif isinstance(value, float):
                code.append(f"PUSHF {value}")
            elif isinstance(value, str):
                code.append(f'PUSHS "{value}"')
            elif isinstance(value, tuple):
                val_code = self.translate(value)
                if val_code:
                    code.extend(val_code.splitlines())

            code.append(f"STOREG {idx}")

        return "\n".join(code)

    
    def gen_index_or_call(self, node):
        _, name, indices_or_args = node
        code = []

        # Determinar se é acesso a array ou chamada de função
        try:
            is_array = self.symbol_table.is_array(name)
        except Exception:
            is_array = False

        if is_array:
            # --- Acesso a elemento de array ---
            # Em EWVM, arrays são armazenados a partir do endereço gp[idx].
            # O endereço do elemento i é: (gp + idx) + (i - 1)
            arr_idx = self.symbol_table.get_index(name)
            code.append("PUSHGP")            
            code.append(f"PUSHI {arr_idx}")  
            code.append("PADD")              

            # Calcular o índice do elemento
            index_expr = indices_or_args[0] if indices_or_args else 0
            if isinstance(index_expr, tuple):
                index_code = self.translate(index_expr)
                if index_code:
                    code.extend(index_code.splitlines())
            elif isinstance(index_expr, int):
                code.append(f"PUSHI {index_expr}")
            elif isinstance(index_expr, str):
                idx_i = self.symbol_table.get_index(index_expr)
                code.append(f"PUSHG {idx_i}")

            code.append("PUSHI 1")
            code.append("SUB")
            code.append("PADD")     
            code.append("LOAD 0")   # ler o valor no endereço calculado
        else:
            # --- Chamada de função ---
            # Funções em Fortran também recebem argumentos por referência.
            # Para cada argumento, empurrar o seu endereço (PUSHGP + offset + PADD).
            for arg in indices_or_args:
                if isinstance(arg, str):
                    idx = self.symbol_table.get_index(arg)
                    code.append("PUSHGP")
                    code.append(f"PUSHI {idx}")
                    code.append("PADD")
                elif isinstance(arg, int):
                    code.append(f"PUSHI {arg}")
                elif isinstance(arg, float):
                    code.append(f"PUSHF {arg}")
                elif isinstance(arg, tuple):
                    arg_code = self.translate(arg)
                    if arg_code:
                        code.extend(arg_code.splitlines())

            code.append(f"PUSHA FUNC_{name}")
            code.append("CALL")

        return "\n".join(code)
    


    # label, stop, concat, declare
    def gen_label(self, node):
        _, label_name = node
        scope_name = self.symbol_table.get_current_scope()
        full_label_name = f"{scope_name}_{label_name}"
        return [full_label_name + ":"]
    
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
        code.append(self.translate(left))
        code.append(self.translate(right))
        code.append("CONCAT")
        return code
    
    def gen_write(self, node):
        _, control_spec, args = node
        code = []

        # WRITE(*,*) sem argumentos -> linha vazia
        if not args:
            code.append('PUSHS "\\n"')
            code.append("WRITES")
            return "\n".join(code)

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
                arg_code = self.translate(arg)
                if arg_code:
                    code.extend(arg_code.splitlines())

                expr_type = self.symbol_table.get_expr_type(arg)

                if expr_type in ("REAL", "DOUBLE"):
                    code.append("WRITEF")
                elif expr_type in ("CHARACTER", "STRING"):
                    code.append("WRITES")
                else:
                    code.append("WRITEI")

        code.append('PUSHS "\\n"')
        code.append("WRITES")

        return "\n".join(code)