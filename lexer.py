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
    "CHARACTER": "CHARACTER",
    "PARAMETER": "PARAMETER", # PARAMETER define uma constante, enquanto x = 10 define uma variável.
    "LABEL": "LABEL"
}

tokens = ["INT", "NREAL", "BOOL", "LT", "GT", "LE", "GE", "EQ", "NE", "VAR", "DOUBLE",
          "OPADDSUB", "OPDIV", "AND", "OR", "NOT", "EQUALS", "STRING", "POWER", "CONCAT"]+ list(reserved.values())


def t_COMMENT(t):
    # capturar o comentário inteiro (o resto da linha)
    r'(^|\n)[cC*].*'
    # t.value = t.value[7:] # ignorar \n + o conteúdo nas colunas reservadas
    # return t
    pass # ignorar os comentários, não precisamos deles para a análise sintática

def t_DOUBLE(t):
    r"DOUBLE\s+PRECISION"
    t.value = "DOUBLE PRECISION"
    return t

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
    r"[A-Za-z_][A-Za-z0-9_]*"
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


class LexError(Exception):
    pass
    
def t_error(t): 
    raise LexError(f"Illegal character '{t.value[0]}' at line {t.lexer.lineno}")


lexer = lex.lex()



def main(args):
    with open(args[1], "r") as f:
        data = f.read()
    try: 
        lexer.input(data)
        for tok in lexer:
            print(tok)
    except Exception as e:
        print(f"Erro de análise léxica: {e}")

if __name__ == "__main__":
    main(sys.argv)

# comentários - ju
# labels - sofia

# formatação in-line (ex: '(A, I5)') - su
# geral - su