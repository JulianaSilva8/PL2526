import ply.lex as lex
import sys

reserved = {
    "PROGRAM": "PROGRAM",
    "END": "END",
    "ELSE": "ELSE",
    "IF": "IF",
    "ENDIF": "ENDIF",
    "CONTINUE": "CONTINUE",
    "THEN": "THEN",
    "RETURN": "RETURN",
    "FUNCTION": "FUNCTION",
    "DO": "DO",
    "GOTO": "GOTO",
    "PRINT": "PRINT",
    "READ": "READ",
    "INTEGER": "INTEGER",
    "REAL": "REAL",
    "LOGICAL": "LOGICAL",
    "MOD": "MOD",
    "STOP": "STOP",
    "WRITE": "WRITE",
    "DOUBLE": "DOUBLE",
    "PRECISION": "PRECISION",
    "CHARACTER": "CHARACTER",
    "PARAMETER": "PARAMETER",
}

tokens = ["INT", "COMMENT", "NREAL", "BOOL", "LT", "GT", "LE", "GE", "EQ", "NE", "VAR", 
          "OPADDSUB", "OPDIV", "AND", "OR", "NOT", "EQUALS", "STRING", "POWER", "CONCAT"]+ list(reserved.values())

def t_COMMENT(t):
    r"\nC\s"
    t.value = "C"
    return t

# def t_COMMENT(t):
#     r"[Cc\*].*"
#     pass

def t_NREAL(t):
    r"\d+\.\d*"
    t.value = float(t.value) 
    return t

def t_INT(t):
    r"\d+"
    t.value = int(t.value) 
    return t

def t_BOOL(t):
    r"\.TRUE\.|\.FALSE\."
    if t.value.upper() == ".TRUE.":
        t.value = True
    else:
        t.value = False
    return t

def t_newline(t):
    r"\n+"
    t.lexer.lineno += 1 

def t_VAR(t):
    r"[A-Za-z][A-Za-z0-9_]*"
    t.type = reserved.get(t.value, "VAR") 
    return t

def t_STRING(t):
    r'\'[^\']*\''
    t.value = t.value[1:-1]
    return t

literals = "(),*'"

t_CONCAT = r"//" # operador de concatenação
t_POWER = r"\*\*" # operador de potência
t_OPADDSUB = r"[+\-]" # operadores de adição e subtração
t_OPDIV = r"/" # operadores de multiplicação e divisão
t_EQUALS = r"=" # operador de atribuição
t_EQ = r'\.EQ\.'
t_NE = r'\.NE\.'
t_LT = r'\.LT\.'
t_LE = r'\.LE\.'
t_GT = r'\.GT\.'
t_GE = r'\.GE\.'
t_AND = r'\.AND\.'
t_OR = r'\.OR\.'
t_NOT = r'\.NOT\.'
t_ignore = " \t"

def t_error(t): 
    print("Invalid symbol:", t.value[0])
    t.lexer.skip(1)

lexer = lex.lex()

def main(args):
    with open(args[1], "r") as f:
        data = f.read()
    lexer.input(data)
    for tok in lexer:
        print(tok)

if __name__ == "__main__":
    main(sys.argv)