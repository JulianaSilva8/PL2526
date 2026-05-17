import ply.lex as lex
import sys
from errors import LexError

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
    "SUBROUTINE": "SUBROUTINE",
    "CALL": "CALL",
    "DO": "DO",
    "GOTO": "GOTO",
    "PRINT": "PRINT",
    "READ": "READ",
    "INTEGER": "INTEGER",
    "REAL": "REAL",
    "LOGICAL": "LOGICAL",
    "MOD": "MOD",
    "STOP": "STOP",
    "CHARACTER": "CHARACTER",
    "PARAMETER": "PARAMETER", # PARAMETER define uma constante, enquanto x = 10 define uma variável.
}

tokens = ["LABEL", "INT", "NREAL", "BOOL", "LT", "GT", "LE", "GE", "EQ", "NE", "VAR", 
          "OPADDSUB", "OPDIV", "AND", "OR", "NOT", "EQUALS", "STRING", "POWER", "CONCAT", "CONTINUATION"]+ list(reserved.values())


def t_COMMENT(t):
    r'(?m:^[cC*].*)'
    pass # ignorar os comentários, não precisamos deles para a análise sintática

def t_NREAL(t):
    r"(?:\d+\.\d*|\.\d+)(?:[eEdD][+\-]?\d+)?"
    t.value = float(t.value.replace('D', 'E').replace('d', 'E')) 
    t.value = float(t.value) 
    return t

def t_LABEL(t):
    r"\d+"
    s = t.value
    data = t.lexer.lexdata  # o texto completo que está sendo analisado
    pos = t.lexpos  # a posição atual do token no texto (índice do primeiro caractere do token)
    last_nl = data.rfind('\n', 0, pos) # posição do último \n antes do token, ou -1 se não houver \n
    col = pos - last_nl # 1-based column
    if col <= 5 and len(s) <= 5: # labels devem estar nas colunas 1-5 e ter no máximo 5 dígitos
        t.type = "LABEL"
        t.value = int(s)
        return t
    t.type = "INT"
    t.value = int(s)
    return t

def t_INT(t):
    r"\d+"
    t.value = int(t.value) 
    return t

def t_BOOL(t):
    r"\.TRUE\.|\.true\.|\.FALSE\.|\.false\."
    if t.value.upper() == ".TRUE.":
        t.value = True
    else:
        t.value = False
    return t

def t_CONTINUATION(t):
    r'\n[ ]{5}[^0\s]'
    t.lexer.lineno += 1
    pass

def t_newline(t):
    r"\n+"
    t.lexer.lineno += 1 

def t_VAR(t):
    r"[A-Za-z_][A-Za-z0-9_]*"

    t.value = t.value.upper()
    t.type = reserved.get(t.value, "VAR")

    return t

def t_STRING(t):
    r'\'[^\']*\''
    #  aspas não removidas para depois conseguir fazer distinção de VARs na analise semântica
    return t

t_CONCAT = r"//" # operador de concatenação
t_POWER = r"\*\*" # operador de potência
t_OPADDSUB = r"[+\-]" # operadores de adição e subtração
t_OPDIV = r"/" # operadores de divisão
t_EQUALS = r"=" # operador de atribuição
t_EQ = r'\.EQ\.|\.eq\.'
t_NE = r'\.NE\.|\.ne\.'
t_LT = r'\.LT\.|\.lt\.'
t_LE = r'\.LE\.|\.le\.'
t_GT = r'\.GT\.|\.gt\.'
t_GE = r'\.GE\.|\.ge\.'
t_AND = r'\.AND\.|\.and\.'
t_OR = r'\.OR\.|\.or\.'
t_NOT = r'\.NOT\.|\.not\.'
t_ignore = " \t"

literals = "(),*'"

def check_indentation(data):
    """Valida a indentação fixed-form: colunas 1-5 só podem conter labels."""
    lines = data.split('\n')
    for i, line in enumerate(lines):
        if not line.strip() or line[0].upper() in ['C', '*']:
            continue
    
        l = line.replace('\t', '      ')  # contar tabs como 6 espaços
        label_area = l[0:5]      # colunas 1-5

        # antes de 6 só labels
        content = label_area.strip()
        if content:
            if not content.isdigit():
                raise LexError(f"Erro de indentação na linha {i+1}: Colunas 1-5 devem reservadas para labels")
    return data

def t_error(t): 
    """Lança erro quando encontra um carácter ilegal."""
    raise LexError(f"Illegal character '{t.value[0]}' at line {t.lexer.lineno}")

lexer = lex.lex()

def main(args):
    """Executa o lexer sobre um ficheiro e imprime a sequência de tokens."""
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
