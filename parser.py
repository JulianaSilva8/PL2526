import sys

from ply import lex, yacc
from lexer import lexer


def p_declaration(p):
    r"""
    Declaration : Type VarList
    VarList : VAR
            | VarList "," VAR
    Type : INTEGER
         | REAL
         | LOGICAL
         | DOUBLE
         | CHARACTER
    """

def p_expression_binop(p):
    r"""
    Expression : Expression OPADDSUB Expression
               | Expression OPDIV Expression
               | Expression POWER Expression
               | Expression CONCAT Expression
               | Expression AND Expression
               | Expression OR Expression
               | Expression NOT Expression
               | Expression LT Expression
               | Expression GT Expression
               | Expression LE Expression
               | Expression GE Expression
               | Expression EQ Expression
               | Expression NE Expression
               | Expression MOD Expression
               | Expression : "(" Expression ")"
               | ExpressionElement
    """

def p_expression_element(p):
    r"""
    ExpressionElement : VAR
                      | INT
                      | NREAL
                      | BOOL
                      | STRING
    """
def p_if_statement(p):
    r"""
    IfStatement : IF Expression THEN StatementList ENDIF
                | IF Expression THEN StatementList ELSE StatementList ENDIF
    """

def p_for_statement(p):
    r"""
    ForStatement : DO LABEL VAR EQUALS Expression TO Expression StatementList
    """

def p_function_call(p):
    r"""
    FunctionCall : VAR "(" ArgList ")"
    ArgList : Expression
            | ArgList "," Expression
            | empty
    """

def p_function_declaration(p):
    r"""
    FunctionDeclaration : Type FUNCTION VAR "(" ParamList ")" StatementList RETURN END
    ParamList : Type VAR
              | ParamList "," Type VAR
              | empty
    """

def p_statement_continue(p):
    r"""
    Continue: LABEL CONTINUE
    """

def p_goto_statement(p):
    r"""
    GotoStatement : GOTO LABEL
    """

def p_print_statement(p):
    r"""
    PrintStatement : PRINT Format ArgList
    """

def p_read_statement(p):
    r"""
    ReadStatement : READ Format VarList
    """
def p_format(p):
    r"""
    Format : "*"
    """
    #         | INT_CONST
    #         | STRING_LITERAL
    # """
    # TIMES é o '*'
    # INT_CONST é o label (ex: 100)
    # STRING_LITERAL é a formatação in-line (ex: '(A, I5)')

def p_assignment(p):
    r"""
    Assignment : VAR EQUALS Expression
    """

def p_parse(p):
    r"""
    Program : PROGRAM VAR StatementList END
            | PROGRAM VAR NEWLINE StatementList END COMMENT
    StatementList : Statement
                  | StatementList Statement
    Statement : Declaration
              | Assignment
              | IfStatement
              | WhileStatement
              | ForStatement
              | FunctionCall
              | ReturnStatement
              | GotoStatement
              | PrintStatement
              | ReadStatement
    """

class ParseError(Exception):
    pass

def p_error(t):
    raise ParseError(f"Unexpected token: {t.type if t else '$'}")

# Build parser
parser = yacc.yacc()
parser.vars = {} # inicializar o dicionário!!!
parser.quit = False


def main(args):
    with open(args[1], "r") as f:
        data = f.read()
    try: 
        lexer.input(data)
        parser.parse(data, lexer=lexer)
        for tok in lexer:
            print(tok)
    except Exception as e:
        print(f"Erro de análise léxica: {e}")

if __name__ == "__main__":
    main(sys.argv)