
class Translator:
    def __init__(self, symbol_table):
        self.symbol_table = symbol_table        
        self.label_count = 0
        self.current_scope = None # None - escopo global, ou nome da função/subrotina atual
        self.variables = {}
        self.next_addr = 0

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
        elif op == 'DO':                         # JU
            return self.gen_do(node)
        elif op == 'GOTO':                       # JU
            return self.gen_goto(node)
        elif op == 'LABEL':                      # SORAIA
            return self.gen_label(node)
        elif op == 'CALL':                       #   SOFIA
            return self.gen_call(node)
        elif op == 'READ':                       #  JU
            return self.gen_read(node)
        elif op == 'STOP':                       # SORAIA
            return self.gen_stop(node)
        elif op == 'WRITE':                       #  SOFIA
            return self.gen_write(node)
        elif op == 'CONTINUE':                     # JU
            return self.gen_continue(node)
        elif op == 'PRINT':                          #   JU    
            return self.gen_print(node)
        elif op in ('ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'POWER'): #  JU
            return self.gen_arithmetic(node, op)
        elif op in ('LT', 'GT', 'LE', 'GE', 'EQ', 'NE'):        #   SOFIA
            return self.gen_relational(node)
        elif op in ('AND', 'OR'):                               #   SOFIA
            return self.gen_logical(node)
        elif op == 'NOT':                                       # JU
            return self.gen_not(node)
        elif op == 'CONCAT':                                    # SORAIA
            return self.gen_concat(node)
        elif op == 'PARAMETER':                                 #   SOFIA
            return self.gen_parameter(node)
        elif op == 'INDEX_OR_CALL':                             #   SOFIA
            return self.gen_index_or_call(node)

        return ["// Unhandled node: " + str(op)]

    def allocate_vars(self):
        table = self.symbol_table.get_table()
        code = []
        vars = self.symbol_table.get_table()
        for name, value in vars.items():
            if value['is_parameter'] or value['is_label']:
                continue # já inicializados
            
            if value['is_array']:
                size = value['size']
                code.append(f"ALLOC {size}") # ver!!!!!!!!
            else:
                if value['type'] == 'INTEGER':
                    code.append("PUSHI 0")
                elif value['type'] == 'REAL':
                    code.append("PUSHF 0.0")
                elif value['type'] == 'BOOL':
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
                elif type == 'BOOL':
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
        _, fmt, args = node
        code = []
        for arg in args:
            code.append(self.translate(arg))
            code.append("PRINT_VAL")
        return "\n".join(code)

    def gen_arithmetic(self, node, instr):
        _, left, right = node
        return f"{self.translate(left)}\n{self.translate(right)}\n{instr}"
    


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
    