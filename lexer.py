import ply.lex as lex

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
    "READ": "READ"
}

tokens = ["INTEGER", "REAL", "LOGICAL", "LT", "GT", "LE", "GE", "EQ", "NE", "VAR", 
          "OPADDSUB", "OPMULDIV", "AND", "OR", "NOT", "TRUE", "FALSE", 
          "STRING"]+ list(reserved.values())

def t_REAL(t):
    r"\d+\.\d+"
    t.value = float(t.value)
    return t

def t_INTEGER(t): 
    r"\d+"
    t.value = int(t.value) 
    return t

def t_LOGICAL(t):
    r"(.TRUE.|.FALSE.)"
    t.value = bool(t.value)
    return t

def t_newline(t):
    r"\n+"
    t.lexer.lineno += 1 

def t_VAR(t):
    r"[a-zA-Z0-9]+"
    t.type = reserved.get(t.value, "VAR") 
    return t

def t_STRING(t):
    r'\'[^\']*\''
    t.value = t.value[1:-1]
    return t

literals = "(),*'"

t_OPADDSUB = r"[+\-]" # operadores de adição e subtração
t_OPMULDIV = r"[/\*]" # operadores de multiplicação e divisão
t_EQ = r'\.EQ\.'
t_NE = r'\.NE\.'
t_LT = r'\.LT\.'
t_LE = r'\.LE\.'
t_GT = r'\.GT\.'
t_GE = r'\.GE\.'
t_AND = r'\.AND\.'
t_OR = r'\.OR\.'
t_NOT = r'\.NOT\.'
t_TRUE = r'\.TRUE\.'
t_FALSE = r'\.FALSE\.'
t_ignore = " \t"

def t_error(t): 
    print("Invalid symbol:", t.value[0])
    t.lexer.skip(1)

lexer = lex.lex()

ex1 = """
    PROGRAM HELLO
    PRINT *, 'Ola, Mundo!'
    END
"""
lexer.input(ex1)
for tok in lexer:
    print(tok)
