import sys

from ply import lex, yacc
from lexer import lexer, tokens
from symbol_table import SymbolTable

def p_declaration(p):
    r"""
    Declaration : Type VarList
    """
    type_name = p[1]
    for var in p[2]:
        if isinstance(var, tuple):  # array decl
            var_name, size = var
            parser.symbol_table.add_variable(var_name, type_name, is_array=True, size=size)
        else:  # regular variable declaration
            parser.symbol_table.add_variable(var, type_name)


def p_var_decl(p):
    r"""
    VarDecl : VAR
    """
    p[0] = p[1]

def p_var_decl_array(p):
    r"""
    VarDecl : VAR "(" INT ")"
    """
    p[0] = (p[1], p[2])

def p_var_list_single(p):
    r"""
    VarList : VarDecl
    """
    p[0] = [p[1]]


def p_var_list(p):
    r"""
    VarList : VarList "," VarDecl
    """
    p[0] = p[1] + [p[3]]
    

def p_type(p):
    r"""
    Type : INTEGER
         | REAL
         | LOGICAL
         | DOUBLE
         | CHARACTER
    """

def p_parameter_statement(p):
    r"""
    ParameterStatement : PARAMETER "(" ParamAssignList ")"
    """

def p_param_assign_list(p):
    r"""
    ParamAssignList : ParamAssign
                    | ParamAssignList "," ParamAssign
    """

def p_param_assign(p):
    r"""
    ParamAssign : VAR EQUALS Expression
    """

# ver: parenteses nas expressões e NOT

# hierarquia de operadores:
# 1. Logical: AND, OR, NOT
# 2. Relational: LT, GT, LE, GE, EQ, NE
# 3. Additive: OPADDSUB
# 4. Multiplicative: OPDIV, MOD
# 5. Power: POWER
# 6. Concatenation: CONCAT


def p_logical_expression(p):
    r"""
    Expression : LogicalTerm
               | Expression OR LogicalTerm
    """

def p_logical_term(p):
    r"""
    LogicalTerm : LogicalFactor
                | LogicalTerm AND LogicalFactor
    """

def p_logical_factor(p):
    r"""
    LogicalFactor : NOT LogicalFactor
                  | NonLogicalExpression
    """

# JU !!!!!!!1
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
         | Term '*' PowerExpression
         | MOD "(" Term "," PowerExpression ")"
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
                      | IndexOrCall
                      | INT
                      | NREAL
                      | BOOL
                      | STRING
                      | "(" Expression ")"
    """


def p_if_statement(p):
    r"""
    IfStatement : IF Expression THEN StatementList ENDIF
                | IF Expression THEN StatementList ELSE StatementList ENDIF
                | IF Expression StatementContent
    """

def p_for_statement(p): # não é suppsto incluir os statements dentro do for -> isso é tratado na análise semântica
    r"""
    ForStatement : DO INT VAR EQUALS Expression "," Expression
    """

def p_arg_list(p):
    r"""
    ArgList : Expression
            | ArgList "," Expression
    """

def p_function_declaration(p):
    r"""
    FunctionDeclaration : Type FUNCTION IndexOrCall StatementList RETURN END
    """


def p_index_or_call(p):
    r"""
    IndexOrCall : VAR "(" ArgList ")"
                | VAR "(" ")"
    """

def p_continue(p):
    r"""
    Continue : CONTINUE
    """

def p_goto_statement(p):
    r"""
    GotoStatement : GOTO INT
    """

def p_stop_statement(p): # args opcionais: String of no more that 5 digits or a character constant 
    r"""
    StopStatement : STOP STRING
                  | STOP INT
                  | STOP
    """

# SOFIA !! 
def p_print_statement(p): # print sem args -> linha vazia 
    r"""
    PrintStatement : PRINT Format "," ArgList
                   | PRINT Format
    """

def p_read_arg(p):
    r"""
    ReadArg : VAR
            | IndexOrCall
    """

def p_read_arg_list(p):
    r"""
    ReadArgList : ReadArg
                | ReadArgList "," ReadArg
    """

def p_read_statement(p):
    r"""
    ReadStatement : READ Format "," ReadArgList
    """

# def p_write_statement(p): # SEE
#     r"""
#     WriteStatement : WRITE "(" ControlPair ")" ArgList
#                     | WRITE "(" ControlPair ")"
#     """

# def p_control_pair(p):
#     r"""
#     ControlPair : Expression "," Expression
#                 | "*" "," Expression
#                 | Expression "," "*"
#                 | "*" "," "*"
#     """

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
    Statement : StatementContent
    """

    #           | WriteStatement  -> SEE LATER
    # """

def p_label_statement(p):
    r"""
    Statement : LABEL StatementContent
    """

def p_program_unit(p):
    r"""
    ProgramUnit : Program
                | FunctionDeclaration
    """

def p_statement_content(p):
    r"""
    StatementContent : Declaration
                        | Assignment
                        | IfStatement
                        | ForStatement
                        | GotoStatement
                        | PrintStatement
                        | ReadStatement
                        | ParameterStatement
                        | Continue
                        | StopStatement
    """

def p_parse(p):
    r"""
    ProgramUnitList : ProgramUnitList ProgramUnit
                    | ProgramUnit
    """

class ParseError(Exception):
    pass

class SemanticError(Exception):
    pass

def p_error(t):
    raise ParseError(f"Parse Error: Unexpected token: {t.type if t else '$'} (token value: {t.value}) at line {t.lineno if t else 'EOF'}")

# Build parser
parser = yacc.yacc(start="ProgramUnitList", write_tables=False)
parser.symbol_table = SymbolTable()
parser.quit = False


def main(args):
    with open(args[1], "r") as f:
        data = f.read()
    try: 
        parser.parse(data, lexer=lexer)
        for tok in lexer:
            print(tok)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main(sys.argv)


# STOP str (String of no more that 5 digits or a character constant) - para o prog e mostra a str
# VAR