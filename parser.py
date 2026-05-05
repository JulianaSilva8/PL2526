import sys

from ply import lex, yacc
from lexer import lexer, tokens
from symbol_table import SymbolTable
from errors import ParseError, SemanticError

def p_declaration(p):
    r"""
    Declaration : Type VarList
    """
    type_name = p[1]
    vars_declared = []
    for var in p[2]:
        if isinstance(var, tuple):  # array decl
            var_name, size = var
            parser.symbol_table.add_symbol(var_name, type_name, is_array=True, size=size)
            vars_declared.append((var_name, type_name, size))
        else:  # regular variable declaration
            parser.symbol_table.add_symbol(var, type_name)
            vars_declared.append((var, type_name))
    p[0] = ('DECLARE', type_name, vars_declared)


def p_var_decl(p):
    r"""
    VarDecl : VAR
    """
    p[0] = p[1]

def p_var_decl_array(p):
    r"""
    VarDecl : VAR "(" INT ")"
    """
    p[0] = (p[1], p[3])

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
    p[0] = p[1] 

def p_parameter_statement(p):
    r"""
    ParameterStatement : PARAMETER "(" ParamAssignList ")"
    """
    params = []
    for var, value in p[3]:
        parser.symbol_table.add_symbol(var, is_parameter=True)
        parser.symbol_table.update_symbol(var, value)
        params.append((var, value))
    p[0] = ('PARAMETER', params)

def p_param_assign_list(p):
    r"""
    ParamAssignList : ParamAssign
                    | ParamAssignList "," ParamAssign
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_param_assign(p):
    r"""
    ParamAssign : VAR EQUALS Expression
    """
    p[0] = (p[1], p[3])

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
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ('OR', p[1], p[3])

def p_logical_term(p):
    r"""
    LogicalTerm : LogicalFactor
                | LogicalTerm AND LogicalFactor
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ('AND', p[1], p[3])

def p_logical_factor(p):
    r"""
    LogicalFactor : NOT LogicalFactor
                  | NonLogicalExpression
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ('NOT', p[2])

# JU !!!!!!!1
def p_nonlogical_expression(p):
    r"""
    NonLogicalExpression : AdditiveExpression
                        | AdditiveExpression RelationalOp AdditiveExpression
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = (p[2], p[1], p[3])

def p_relational_op(p):
    r"""
    RelationalOp : LT
                 | GT
                 | LE
                 | GE
                 | EQ
                 | NE
    """
    p[0] = p.slice[1].type # para ter LE e não .LE.

def p_additive_expression(p):
    r"""
    AdditiveExpression : Term
                       | AdditiveExpression OPADDSUB Term
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = (p[2], p[1], p[3])


def p_multiplicative_expression(p):
    r"""
    Term : PowerExpression
         | Term OPDIV PowerExpression
         | Term '*' PowerExpression
         | MOD "(" Term "," PowerExpression ")"
    """
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 7:
        p[0] = ('MOD', p[3], p[5])
    else:
        p[0] = (p[2], p[1], p[3])

def p_power_expression(p):
    r"""
    PowerExpression : ConcatenationExpression
                    | PowerExpression POWER ConcatenationExpression
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ('POWER', p[1], p[3])

def p_concatenation_expression(p):
    r"""
    ConcatenationExpression : ExpressionElement
                          | ConcatenationExpression CONCAT ExpressionElement
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ('CONCAT', p[1], p[3])

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
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[2]

def p_if_statement(p):
    r"""
    IfStatement : IF Expression THEN StatementList ENDIF
                | IF Expression THEN StatementList ELSE StatementList ENDIF
                | IF Expression StatementContent
    """
    if len(p) == 6:
        p[0] = ('IF', p[2], p[4], None)
    elif len(p) == 8:
        p[0] = ('IF', p[2], p[4], p[6])
    else:
        p[0] = ('IF', p[2], [p[3]], None)



def p_for_statement(p): # não é suppsto incluir os statements dentro do for -> isso é tratado na análise semântica
    r"""
    ForStatement : DO INT VAR EQUALS Expression "," Expression
                 | DO INT VAR EQUALS Expression "," Expression "," Expression
    """
    if len(p) == 8:
        p[0] = ('DO', p[2], p[3], p[5], p[7], 1)  # default step = 1
    else:
        p[0] = ('DO', p[2], p[3], p[5], p[7], p[9])

def p_arg_list(p):
    r"""
    ArgList : Expression
            | ArgList "," Expression
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_function_declaration(p):
    r"""
    FunctionDeclaration : Type FUNCTION IndexOrCall StatementList RETURN END
                        | Type FUNCTION IndexOrCall StatementList END
    """
    if len(p) == 7:
        p[0] = ('FUNCTION', p[1], p[3], p[4])
    else:
        p[0] = ('FUNCTION', p[1], p[3], p[4])  # implicit RETURN
    parser.symbol_table = SymbolTable()  # Reset for next program unit

def p_subroutine_declaration(p):
    r"""
    SubroutineDeclaration : SUBROUTINE VAR StatementList END
                          | SUBROUTINE VAR "(" ArgList ")" StatementList END
                          | SUBROUTINE VAR "(" ")" StatementList END
    """
    if len(p) == 5:
        # SUBROUTINE VAR StatementList END
        p[0] = ('SUBROUTINE', p[2], [], p[3])
    elif len(p) == 8:
        # SUBROUTINE VAR "(" ArgList ")" StatementList END
        p[0] = ('SUBROUTINE', p[2], p[4], p[6])
    else:
        # SUBROUTINE VAR "(" ")" StatementList END
        p[0] = ('SUBROUTINE', p[2], [], p[5])
    parser.symbol_table = SymbolTable()  # Reset for next program unit

def p_call_statement(p):
    r"""
    CallStatement : CALL VAR
                  | CALL VAR "(" ArgList ")"
                  | CALL VAR "(" ")"
    """
    if len(p) == 3:
        # CALL VAR
        p[0] = ('CALL', p[2], [])
    elif len(p) == 6:
        # CALL VAR "(" ArgList ")"
        p[0] = ('CALL', p[2], p[4])
    else:
        # CALL VAR "(" ")"
        p[0] = ('CALL', p[2], [])

def p_index_or_call(p):
    r"""
    IndexOrCall : VAR "(" ArgList ")"
                | VAR "(" ")"
    """
    if len(p) == 5:
        p[0] = ('INDEX_OR_CALL', p[1], p[3])
    else:
        p[0] = ('INDEX_OR_CALL', p[1], [])

def p_continue(p):
    r"""
    Continue : CONTINUE
    """
    p[0] = ('CONTINUE',)

def p_goto_statement(p):
    r"""
    GotoStatement : GOTO INT
    """
    p[0] = ('GOTO', p[2])

def p_stop_statement(p): # args opcionais: String of no more that 5 digits or a character constant 
    r"""
    StopStatement : STOP STRING
                  | STOP INT
                  | STOP
    """
    if len(p) == 2:
        p[0] = ('STOP', None)
    else:
        p[0] = ('STOP', p[2])

# SOFIA !! 
def p_print_statement(p): # print sem args -> linha vazia 
    r"""
    PrintStatement : PRINT Format "," ArgList
                   | PRINT Format
    """
    if len(p) == 3:
        # PRINT Format
        p[0] = ('PRINT', p[2], [])
    else:
        # PRINT Format , ArgList
        p[0] = ('PRINT', p[2], p[4])

def p_read_arg(p):
    r"""
    ReadArg : VAR
            | IndexOrCall
    """
    p[0] = p[1]

def p_read_arg_list(p):
    r"""
    ReadArgList : ReadArg
                | ReadArgList "," ReadArg
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_read_statement(p):
    r"""
    ReadStatement : READ Format "," ReadArgList
    """
    # READ Format , ReadArgList
    p[0] = ('READ', p[2], p[4])

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
           | INT
           | STRING
    """
    p[0] = p[1]

def p_assignment(p):
    r"""
    Assignment : VAR EQUALS Expression
    """
    p[0] = ('ASSIGN', p[1], p[3])

def p_program(p):
    r"""
    Program : PROGRAM VAR StatementList END
    """
    p[0] = ('PROGRAM', p[2], p[3])
    parser.symbol_table = SymbolTable()  # Reset for next program unit

def p_statement_list(p):
    r"""
    StatementList : Statement
                  | StatementList Statement
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_statement(p):
    r"""
    Statement : StatementContent
    """
    p[0] = p[1]
    #           | WriteStatement  -> SEE LATER
    # """

def p_label_statement(p):
    r"""
    Statement : LABEL StatementContent
    """
    p[0] = ('LABEL', p[1], p[2])

def p_program_unit(p):
    r"""
    ProgramUnit : Program
                | FunctionDeclaration
                | SubroutineDeclaration
    """
    p[0] = p[1]

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
                        | CallStatement
    """
    p[0] = p[1]

def p_parse(p):
    r"""
    ProgramUnitList : ProgramUnitList ProgramUnit
                    | ProgramUnit
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

# class ParseError(Exception):
#     pass

# class SemanticError(Exception):
#     pass

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
        result=parser.parse(data, lexer=lexer)
        print(f"{result}")
        for tok in lexer:
            print(tok)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main(sys.argv)


# STOP str (String of no more that 5 digits or a character constant) - para o prog e mostra a str
# VAR