import sys

from ply import lex, yacc
from lexer import lexer, tokens

def p_empty(p):
    'empty :'
    pass

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
         | PARAMETER
    """
    # parameter não deveria estar aqui

# ver: parenteses nas expressões e NOT

# hierarquia de operadores:
# 1. Logical: AND, OR, NOT
# 2. Relational: LT, GT, LE, GE, EQ, NE
# 3. Additive: OPADDSUB
# 4. Multiplicative: OPDIV, MOD
# 5. Power: POWER
# 6. Concatenation: CONCAT


def p_expression(p):
    r"""
    Expression : NonLogicalExpression
                | NonLogicalExpression LogicalOp NonLogicalExpression
    """

def p_logical_op(p):
    r"""
    LogicalOp : AND
              | OR
              | NOT
    """

def p_nonlogical_expression(p):
    r"""
    NonLogicalExpression : AdditiveExpression
                        | AdditiveExpression RelationalOp AdditiveExpression
    """

def p_relational_op(p):
    r"""
    RelationalOp : LT
                 | GT
                 | LE
                 | GE
                 | EQ
                 | NE
    """

def p_additive_expression(p):
    r"""
    AdditiveExpression : Term
                       | AdditiveExpression OPADDSUB Term
    """

def p_multiplicative_expression(p):
    r"""
    Term : PowerExpression
         | Term OPDIV PowerExpression
         | Term MOD PowerExpression
    """

def p_power_expression(p):
    r"""
    PowerExpression : ConcatenationExpression
                    | PowerExpression POWER ConcatenationExpression
    """

def p_concatenation_expression(p):
    r"""
    ConcatenationExpression : ExpressionElement
                          | ConcatenationExpression CONCAT ExpressionElement
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
    ForStatement : DO LABEL VAR EQUALS Expression "," Expression StatementList
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
    Continue : LABEL CONTINUE
    """

def p_goto_statement(p):
    r"""
    GotoStatement : GOTO LABEL
    """

def p_stop_statement(p): # WRONG - FIX!!!
    r"""
    StopStatement : STOP ArgList
    """

def p_print_statement(p):
    r"""
    PrintStatement : PRINT Format ArgList
    """

def p_read_statement(p):
    r"""
    ReadStatement : READ Format VarList
    """

def p_write_statement(p): # WRONG - FIX!!!
    r"""
    WriteStatement : WRITE Format ArgList
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

def p_program(p):
    r"""
    Program : PROGRAM VAR StatementList END
    """

def p_statement_list(p):
    r"""
    StatementList : Statement
                  | StatementList Statement
    """

def p_statement(p):
    r"""
    Statement : Declaration
              | Assignment
              | IfStatement
              | ForStatement
              | FunctionCall
              | GotoStatement
              | PrintStatement
              | ReadStatement
              | Continue
              | StopStatement
              | WriteStatement
    """

def p_program_unit(p):
    r"""
    ProgramUnit : Program
                | FunctionDeclaration
    """

def p_parse(p):
    r"""
    ProgramUnitList : ProgramUnitList ProgramUnit
                    | ProgramUnit
    """

class ParseError(Exception):
    pass

def p_error(t):
    raise ParseError(f"Unexpected token: {t.type if t else '$'}")

# Build parser
parser = yacc.yacc(start="ProgramUnitList", write_tables=False)
parser.vars = {} # inicializar o dicionário!!!
parser.quit = False


def main(args):
    with open(args[1], "r") as f:
        data = f.read()
    try: 
        parser.parse(data, lexer=lexer)
        for tok in lexer:
            print(tok)
    except Exception as e:
        print(f"Erro de análise léxica: {e}")

if __name__ == "__main__":
    main(sys.argv)


# STOP str (String of no more that 5 digits or a character constant) - para o prog e mostra a str
# VAR