
import code
from utils import *

class Translator:
    def __init__(self, symbol_table):
        """Inicializa o tradutor e o estado necessário para gerar código."""
        self.symbol_table = symbol_table        
        self.label_count = 0
        self.current_scope = None # None - escopo global, ou nome da função/subrotina atual
        self.variables = {}
        self.next_addr = 0
        self.pending_do = {} # para armazenar informações de loops DO pendentes (variável, limite inferior, limite superior, passo)
        self.code_to_add = "" # funções auxiliares a ser added no final do código

    def get_push_instruction(self):
        """Devolve PUSHG (global) ou PUSHL (local) conforme o escopo atual."""
        if self.symbol_table.get_current_scope_type() == 'GLOBAL' or self.symbol_table.get_current_scope_type() == 'PROGRAM':
            return "PUSHG"
        else:
            return "PUSHL"

    def translate(self, program_units):
        """Traduz uma lista de unidades (PROGRAM/FUNCTION/SUBROUTINE) para código."""
        code = []
        
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
        return code, self.code_to_add # formatos diferentes, lista de lines + string com código

    def translate_node(self, node):
        """Traduz um nó AST (ou lista de nós) para uma lista de instruções."""
        if isinstance(node, list):
            code = []
            for stmt in node:
                result = self.translate_node(stmt)
                if result:
                    if isinstance(result, list):
                        code.extend(result)
                    else:
                        code.append(result)
            return code
        
        # quando se está num dead loop, ignora-se os statements todos até ao final
        dead_loop_labels = [lbl for lbl, info in self.pending_do.items() if info.get("is_dead")]
        if dead_loop_labels:
            current_dead_label = dead_loop_labels[0]
            
            # se nodo for a label de fim do dead loop, passar à frente
            if isinstance(node, tuple) and node[0] == 'LABEL' and str(node[1]) == str(current_dead_label):
                del self.pending_do[current_dead_label]
                return []
                
            return []

        if not isinstance(node, tuple):
            return self.gen_literals(node)
        op = node[0]
        
        if op == 'DECLARE':                    
            return self.gen_declaration(node)
        elif op == 'ASSIGN':
            return self.gen_assign(node)
        elif op == 'IF':                         
            return self.gen_if(node)
        elif op == 'DO':
            return self.gen_do(node)
        elif op == 'GOTO':
            return self.gen_goto(node)
        elif op == 'LABEL':                      
            return self.gen_label(node)
        elif op == 'CALL':                       
            return self.gen_call(node)
        elif op == 'READ':
            return self.gen_read(node)
        elif op == 'STOP':                       
            return self.gen_stop(node)
        elif op == 'CONTINUE':
            return self.gen_continue(node)
        elif op == 'PRINT':
            return self.gen_print(node)
        elif op in ('ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'POWER'):
            return self.gen_arithmetic(node, op)
        elif op in ('LT', 'GT', 'LE', 'GE', 'EQ', 'NE'):      
            return self.gen_relational(node)
        elif op in ('AND', 'OR'):                              
            return self.gen_logical(node)
        elif op == 'NOT':
            return self.gen_not(node)
        elif op == 'CONCAT':                              
            return self.gen_concat(node)
        elif op == 'PARAMETER':                               
            return self.gen_parameter(node)
        elif op == 'INDEX_OR_CALL':                         
            return self.gen_index_or_call(node)
        elif op == 'RETURN':
            return []

        return ["// Unhandled node: " + str(op)]

    def allocate_vars(self):
        """Gera código para alocar/inicializar variáveis do escopo atual."""
        code = []
        vars = self.symbol_table.get_table(self.current_scope)
        for name, value in vars.items():
            if value['is_label'] or value['is_return_value'] or value['is_formal_param']:
                continue
            
            if value['is_array']:
                if value['type'] == 'CHARACTER':
                    code.append(f'PUSHS ""')
                else:
                    size = value['size']
                    code.append(f"ALLOC {size}")
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
        """Gera o código de um PROGRAM (alocação, corpo e STOP)."""
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
        """Gera o código de uma FUNCTION (parâmetros, locais, corpo e RETURN)."""
        _, type, name, params, body = node
        self.current_scope = name

        code = []
        pop_count = 0
        func_label = f"FUNC{name}"
        code.append(func_label + ":")

        formal_params_count = -len(params)
        for p in params:
            pop_count += 1
            code.append(f"PUSHL {formal_params_count}")
            formal_params_count += 1
        
        self.symbol_table.go_to_scope(name) # entrar no escopo da função

        return_addr = -len(params) - 1
        self.symbol_table.set_return_address(name, return_addr) # reservar posição para valor de retorno da função
        alloc_code =  self.allocate_vars()
        if alloc_code:
            pop_count += len(alloc_code)
            code += alloc_code

        code += self.translate_node(body)

        if pop_count > 0:
            code.append(f"POP {pop_count}") # limpar parâmetros e variáveis locais da pilha antes de retornar

        code.append("RETURN")
        code.append("\n")
        self.symbol_table.go_to_scope(None)

        return code
    
    def gen_subroutine(self, node):
        """Gera o código de uma SUBROUTINE (parâmetros, locais, corpo e RETURN)."""
        _, name, params, body = node
        self.current_scope = name

        pop_count = 0 
        code = []
        func_label = f"SUBROUTINE{name}"
        code.append(func_label + ":")

        formal_params_count = -len(params)
        for p in params:
            pop_count += 1
            code.append(f"PUSHL {formal_params_count}")
            formal_params_count += 1
        
        self.symbol_table.go_to_scope(name) # entrar no escopo da subrotina
        aloc_code = self.allocate_vars()
        if aloc_code:
            pop_count += len(aloc_code)
            code += aloc_code

        code += self.translate_node(body)
        self.symbol_table.go_to_scope(None)

        if pop_count > 0:
            code.append(f"POP {pop_count}") # limpar parâmetros e variáveis locais da pilha antes de retornar
        code.append("RETURN")
        code.append("\n")

        return code
    
    def gen_declaration(self, node): 
        """Ignora DECLARE, pois as alocações são feitas no início da unidade."""
        return None

    def gen_literals(self, value):
        """Gera PUSH de literais (int/float/bool/string) ou carregamento de variável."""
        code = []
        if isinstance(value, bool):
            code.append(f"PUSHI {1 if value else 0}")
        elif isinstance(value, int):
            code.append(f"PUSHI {value}")
        elif isinstance(value, float):
            code.append(f"PUSHF {value}")
        elif isinstance(value, str):
            if value.startswith("'") and value.endswith("'"):
                literal = value[1:-1].replace('"', '\\"')
                code.append(f'PUSHS \"{literal}\"')
            else:
                # caso seja uma variavel
                idx = self.symbol_table.get_index(value)
                code.append(self.get_push_instruction() + " " + str(idx))
        return code

    def gen_assign(self, node):
        """Gera código para atribuições a variáveis e posições de arrays."""
        _, var, expr = node
        # Se expr for um tuplo, traduzimos primeiro a expressão
        code = []
        if isinstance(var, tuple) and var[0] == 'INDEX_OR_CALL': # caso seja um acesso a array, tipo NUMS(I)
            _, var_name, indices = var
            index_expr = indices[0]

            # endereço array
            pos_var = self.symbol_table.get_index(var_name)
            push_inst = self.get_push_instruction()
            code.append(f"{push_inst} {pos_var}") # pilha tem o endereço base do array

            # offset 
            code += self.translate_node(index_expr)
            code.append("PUSHI 1")
            code.append("SUB") # indice em fortran começa em 1

            #storen ordem -> valor, offset, endereço
            code += self.translate_node(expr)

            code.append("STOREN") # a[n] = v
            return code
        #A = 10
        pos_var = self.symbol_table.get_index(var)
        code += self.translate_node(expr)

        if self.symbol_table.is_return_value(var):
            address = self.symbol_table.get_return_address(var)
            code.append(f"STOREL {address}")
        elif self.symbol_table.get_current_scope_type() == 'FUNCTION' or self.symbol_table.get_current_scope_type() =='SUBROUTINE':
            code.append(f"STOREL {pos_var}")
        else:    
            code.append(f"STOREG {pos_var}")
            
        return code
    
    def gen_print(self, node):
        """Gera código para PRINT *, incluindo literais e expressões."""
        _, ast, args = node
        code = []
        if not args: # PRINT * sem argumentos -> imprime lista vazia
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
            elif isinstance(arg, tuple): # PRINT * EXPRESSAO
                code.extend(self.translate_node(arg))
                arg_type = self.symbol_table.get_expr_type(arg)

                if arg_type in ("REAL", "DOUBLE"):
                    code.append("WRITEF")
                elif arg_type in ("CHARACTER", "STRING"):
                    code.append("WRITES")
                else:
                    code.append("WRITEI")
            elif isinstance(arg, str): # PRINT * STRING
                try:
                    idx = self.symbol_table.get_index(arg)
                    var_type = self.symbol_table.get_type(arg)
                    push_inst = self.get_push_instruction()
                    code.append(f"{push_inst} {idx}")

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
                    
        code.append("WRITELN")
        return code

    def gen_arithmetic(self, node, instr):
        """Gera código para operações aritméticas (inclui otimizações simples)."""
        _, left, right = node
        code = []
        is_float = False
        is_power_float = False
        
        if instr == 'POWER':
            if isinstance(left, int):
                self.code_to_add += power_function + "\n"
            elif isinstance(left, float):
                is_power_float = True
                self.code_to_add += power_function_float + "\n"
            code.append("PUSHI 0")

        # otimizações: fazer cálculos caso valores literais
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            if instr == 'ADD':
                return [f"PUSHI {left + right}"] if isinstance(left, int) else [f"PUSHF {left + right}"]
            elif instr == 'SUB':
                return [f"PUSHI {left - right}"] if isinstance(left, int) else [f"PUSHF {left - right}"]
            elif instr == 'MUL':
                return [f"PUSHI {left * right}"] if isinstance(left, int) else [f"PUSHF {left * right}"]
            elif instr == 'DIV':
                return [f"PUSHI {int(left / right)}"] if isinstance(left, int) else [f"PUSHF {left / right}"]
            elif instr == 'MOD':
                return [f"PUSHI {left % right}"]

        # esquerda
        if isinstance(left, tuple):
            code.extend(self.translate_node(left))
            if self.symbol_table.get_expr_type(left) in ("REAL", "DOUBLE", "FLOAT"):
                is_float = True
        elif isinstance(left, bool):
            code.append(f"PUSHI {1 if left else 0}")
        elif isinstance(left, int):
            code.append(f"PUSHI {left}")
        elif isinstance(left, float):
            is_float = True
            code.append(f"PUSHF {left}")
        elif isinstance(left, str):
            idx = self.symbol_table.get_index(left)
            push_inst = self.get_push_instruction()
            code.append(f"{push_inst} {idx}")

        # direita
        if isinstance(right, tuple):
            code.extend(self.translate_node(right))
            if self.symbol_table.get_expr_type(right) in ("REAL", "DOUBLE", "FLOAT"):
                is_float = True
        elif isinstance(right, bool):
            code.append(f"PUSHI {1 if right else 0}")
        elif isinstance(right, int):
            code.append(f"PUSHI {right}")
        elif isinstance(right, float):
            is_float = True
            code.append(f"PUSHF {right}")
        elif isinstance(right, str):
            idx = self.symbol_table.get_index(right)
            push_inst = self.get_push_instruction()
            code.append(f"{push_inst} {idx}")

        if instr == 'POWER':
            if is_power_float:
                code.append("PUSHA POWERFLOAT")
            else: code.append("PUSHA POWER")
            code.append("CALL")
            code.append("POP 2")
            return code

        if is_float:
            op_map = {
                'ADD': 'FADD',
                'SUB': 'FSUB',
                'MUL': 'FMUL',  
                'DIV': 'FDIV',
                'MOD': 'FMOD'
            }
        else:  
            op_map = {
                'ADD': 'ADD',
                'SUB': 'SUB',
                'MUL': 'MUL',
                'DIV': 'DIV',
                'MOD': 'MOD'
            }
        code.append(op_map[instr])
        return code
    
    def gen_not(self, node):
        """Gera código para NOT (com otimização de duplo NOT)."""
        _, expr = node
        
        # Otimização: duplo not
        if isinstance(expr, tuple) and expr[0] == 'NOT':
            print("Aplicando otimização de duplo NOT")
            return self.translate_node(expr[1])
        code = []

        if isinstance(expr, tuple):
            code.extend(self.translate_node(expr))
        elif isinstance(expr, bool):
            code.append(f"PUSHI {1 if expr else 0}")
        elif isinstance(expr, int):
            code.append(f"PUSHI {expr}")
        elif isinstance(expr, str):
            idx = self.symbol_table.get_index(expr)
            push_inst = self.get_push_instruction()
            code.append(f"{push_inst} {idx}")

        code.append("PUSHI 0")
        code.append("EQUAL")
        return code
    
    def gen_read(self, node):
        """Gera código para READ *, suportando variáveis e acessos a arrays."""
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
            
            elif isinstance(arg, tuple) and arg[0] == 'INDEX_OR_CALL':  # 'INDEX_OR_CALL', 'NUMS', ['I'] | READ *, NUMS(I)
                _, name, indices = arg
                
                if len(indices) == 1:

                    idx = self.symbol_table.get_index(name)
                    array_type = self.symbol_table.get_type(name)
                    index_expr = indices[0]
                    push_inst = self.get_push_instruction()
                    code.append(f"{push_inst} {idx}") # Colocar o endereço base do array na pilha

                    # Em Fortran os arrays começam em 1, mas na heap vamos usar índice 0, entao NUMS(I) fica endereço NUMS + (I - 1).
                    if isinstance(index_expr, tuple):
                        code.extend(self.translate_node(index_expr))
                    elif isinstance(index_expr, int):
                        code.append(f"PUSHI {index_expr}")
                    elif isinstance(index_expr, str):
                        idx_index = self.symbol_table.get_index(index_expr)
                        push_inst = self.get_push_instruction()
                        code.append(f"{push_inst} {idx_index}")
                    
                    # Converter índice 1 para índice 0
                    code.append("PUSHI 1")
                    code.append("SUB")

                    code.append("READ")
                    if array_type in ("INTEGER", "LOGICAL"):
                        code.append("ATOI")
                    elif array_type in ("REAL", "DOUBLE"):
                        code.append("ATOF")

                    code.append("STOREN") # armazenar na heap. array[index] = valor
        return code

    def gen_do(self, node):
        """Gera o início de um DO e guarda informação para fechar o loop."""
        _, target_label, var, start, end, step = node
        
        # Otimização
        if isinstance(start, (int, float)) and isinstance(end, (int, float)) and isinstance(step, (int, float)):
            if (step > 0 and start > end) or (step < 0 and start < end):
                print(f"Otimização: loop DO {target_label} não executa")
                
                # info no pending para ignorar statements até à label de fim do loop
                self.pending_do[target_label] = {
                    "is_dead": True
                }
                return [f"// Otimização: Loop {target_label} removido (Dead Loop)"]

        code = []
        
        # gerar labels únicos para o início e fim do loop
        self.label_count += 1
        loop_id = self.label_count
        start_label = f"DO{target_label}{loop_id}START"
        end_label = f"DO{target_label}{loop_id}END"

        # índice da variável de controlo do loop
        var_idx = self.symbol_table.get_index(var)

        # inicializar a var do loop
        if isinstance(start, tuple):
            code.extend(self.translate_node(start))
        elif isinstance(start, int):
            code.append(f"PUSHI {start}")
        elif isinstance(start, float):
            code.append(f"PUSHF {start}")
        elif isinstance(start, str):
            idx = self.symbol_table.get_index(start)
            push_inst = self.get_push_instruction()
            code.append(f"{push_inst} {idx}")

        code.append(f"STOREG {var_idx}")
        code.append(f"{start_label}:")

        # condiçao do loop
        push_inst = self.get_push_instruction()
        code.append(f"{push_inst} {var_idx}") # colocar valor atual da variável de controlo do loop na pilha
        if isinstance(end, tuple):
            code.extend(self.translate_node(end))
        elif isinstance(end, int):
            code.append(f"PUSHI {end}")
        elif isinstance(end, float):
            code.append(f"PUSHF {end}")
        elif isinstance(end, str):
            idx = self.symbol_table.get_index(end)
            push_inst = self.get_push_instruction()
            code.append(f"{push_inst} {idx}")

        code.append("INFEQ") # var > end
        code.append(f"JZ {end_label}") # saltar para o fim do loop

        # guardar info para fechar o loop
        self.pending_do[target_label] = {
            "var": var,
            "var_idx": var_idx,
            "step": step,
            "start_label": start_label,
            "end_label": end_label,
            "is_dead": False
        }
        return code
    
    def gen_continue(self, node):
        """Fecha um DO pendente: incrementa a variável, testa e coloca a label de fim."""
        print("aaaaaaaaaaaaaaaaaaaaaaaaa")
        code = []
        target_label = None

        # Procura qual do_info corresponde à label que acabou de ser impressa
        for label, info in self.pending_do.items():
            # Verifica se esta label é a que está a ser processada agora
            target_label = label
            break 

        if target_label in self.pending_do:
            do_info = self.pending_do[target_label]
            var_idx = do_info['var_idx']
            step = do_info['step']
            start_label = do_info['start_label']
            end_label = do_info['end_label']

            # Incrementar a variável: var = var + step
            push_inst = self.get_push_instruction()
            code.append(f"{push_inst} {var_idx}") 
            if isinstance(step, int):
                code.append(f"PUSHI {step}")
            elif isinstance(step, float):
                code.append(f"PUSHF {step}")
            else: # Se for variável
                s_idx = self.symbol_table.get_index(step)
                push_inst = self.get_push_instruction()
                code.append(f"{push_inst} {s_idx}")
            
            code.append("ADD")
            code.append(f"STOREG {var_idx}")

            # Saltar para o teste de condição no início
            code.append(f"JUMP {start_label}")

            # Colocar a label de saída do loop
            code.append(f"{end_label}:")

            # Limpar o loop pendente
            del self.pending_do[target_label]

        return code

    def gen_goto(self, node):
        """Gera um salto incondicional para uma label no scope atual."""
        _, label = node
        scope_name = self.symbol_table.get_current_scope_name()
        return f"JUMP {scope_name}{label}"
       
    def gen_if(self, node):
        """Gera código para IF/ELSE, com otimização para condição literal."""
        _, cond, then_body, else_body = node
        
        # Otimização
        if isinstance(cond, bool):
            if cond:
                print("Otimização: condição IF é verdadeira, gerando apenas o corpo THEN")
                return self.translate_node(then_body)
            else:
                print("Otimização: condição IF é falsa, gerando apenas o corpo ELSE")
                return self.translate_node(else_body) if else_body else []
        
        code = []

        self.label_count += 1
        if_id = self.label_count
        else_label = f"IF{if_id}ELSE"
        end_label  = f"IF{if_id}END"

        if isinstance(cond, tuple):
            code.extend(self.translate_node(cond))
        elif isinstance(cond, bool):
            code.append(f"PUSHI {1 if cond else 0}")
        elif isinstance(cond, int):
            code.append(f"PUSHI {cond}")
        elif isinstance(cond, str):
            idx = self.symbol_table.get_index(cond)
            push_inst = self.get_push_instruction()
            code.append(f"{push_inst} {idx}")

        code.append(f"JZ {else_label if else_body else end_label}")

        then_code = self.translate_node(then_body)
        if then_code:
            code.extend(then_code)

        if else_body:
            code.append(f"JUMP {end_label}")
            code.append(f"{else_label}:")
            else_code = self.translate_node(else_body)
            if else_code:
                code.extend(else_code)

        code.append(f"{end_label}:")
        return code

    
    def gen_call(self, node):
        """Gera código para CALL a uma subrotina, empilhando argumentos."""
        _, name, args = node
        code = []

        for arg in args:
            if isinstance(arg, tuple):
                code.extend(self.translate_node(arg))
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
                    push_inst = self.get_push_instruction()
                    code.append(f"{push_inst} {idx}")

        code.append(f"PUSHA SUBROUTINE{name}")
        code.append("CALL")
        return code
    
    def gen_relational(self, node):
        """Gera código para operações relacionais (inclui otimização)."""
        op, left, right = node
        
        # Otimização: se ambos os lados forem valores literais
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            ops = {
                'LT': left < right,
                'LE': left <= right,
                'GT': left > right,
                'GE': left >= right,
                'EQ': left == right,
                'NE': left != right
            }
            result = 1 if ops[op] else 0
            print(f"Otimização: expressão relacional com operandos literais, resultado é {result}")
            return [f"PUSHI {result}"]

        code = []
        
        if isinstance(left, tuple):
            left_code = self.translate_node(left)
            if left_code:
                code.extend(left_code)
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
                push_inst = self.get_push_instruction()
                code.append(f"{push_inst} {idx}")

        if isinstance(right, tuple):
            right_code = self.translate_node(right)
            if right_code:
                code.extend(right_code)
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
                push_inst = self.get_push_instruction()
                code.append(f"{push_inst} {idx}")

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
        """Gera código para AND/OR (inclui otimização)."""
        op, left, right = node
        
        # Otimização: se ambos os lados forem booleanos literais
        if isinstance(left, bool) and isinstance(right, bool):
            if op == 'AND':
                res = left and right
            else: # OR
                res = left or right
            print(f"Otimização: expressão lógica com operandos literais, resultado é {res}")
            return [f"PUSHI {1 if res else 0}"]
        
        code = []

        if isinstance(left, tuple):
            code.extend(self.translate_node(left))
        elif isinstance(left, bool):
            code.append(f"PUSHI {1 if left else 0}")
        elif isinstance(left, str):
            idx = self.symbol_table.get_index(left)
            push_inst = self.get_push_instruction()
            code.append(f"{push_inst} {idx}")

        if isinstance(right, tuple):
            code.extend(self.translate_node(right))
        elif isinstance(right, bool):
            code.append(f"PUSHI {1 if right else 0}")
        elif isinstance(right, str):
            idx = self.symbol_table.get_index(right)
            push_inst = self.get_push_instruction()
            code.append(f"{push_inst} {idx}")

        if op == 'AND':
            code.append("MUL")
        else:  # OR
            code.append("ADD")
            code.append("PUSHI 0")
            code.append("GT")

        return code
    
    def gen_parameter(self, node):
        """Ignora PARAMETER na geração: constantes já estão na tabela de símbolos."""
        return "" 

    
    def gen_index_or_call(self, node):
        """Gera acesso a array ou chamada de função."""
        _, name, args = node
        code = []

        if self.symbol_table.is_array(name):
            idx = self.symbol_table.get_index(name)
            push_inst = self.get_push_instruction()
            code.append(f"{push_inst} {idx}")

            index_expr = args[0]
            if isinstance(index_expr, tuple):
                code.extend(self.translate_node(index_expr))
            elif isinstance(index_expr, int):
                code.append(f"PUSHI {index_expr}")
            elif isinstance(index_expr, str):
                idx_i = self.symbol_table.get_index(index_expr)
                push_inst = self.get_push_instruction()
                code.append(f"{push_inst} {idx_i}")

            code.append("PUSHI 1")
            code.append("SUB")
            code.append("LOADN")

        else:
            count_args = 0
            # alocar espaço para o retorno da função
            code.append("PUSHI 0")

            for arg in args:
                if isinstance(arg, tuple):
                    code.extend(self.translate_node(arg))
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
                        push_inst = self.get_push_instruction()
                        code.append(f"{push_inst} {idx}")
                count_args += 1

            code.append(f"PUSHA FUNC{name}")
            code.append("CALL")
            #pop dos args
            if count_args > 0:
                code.append(f"POP {count_args}")

        return code
    
    # label, stop, concat, declare
    def gen_label(self, node):
        _, label_name, statement = node
        scope_name = self.symbol_table.get_current_scope_name()
        full_label_name = f"{scope_name}{label_name}"
        code = [full_label_name + ":"] 
        stmt_code = self.translate_node(statement)

        if stmt_code:
            code += stmt_code

        if label_name in self.pending_do:
            code += self.gen_continue(('CONTINUE',))
            
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
        code += self.translate_node(left)
        code += self.translate_node(right)
        code.append("CONCAT")
        return code