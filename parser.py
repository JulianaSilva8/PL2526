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
    is_string = False

    if isinstance(type_name, tuple):
        type_name, size = type_name
        is_string = True
    else:
        type_name = type_name
    for var in p[2]:
        if isinstance(var, tuple):  # array decl
            if is_string:
                raise SemanticError("Wrong declaration for CHARACTER variable. Size not specified correctly.")
            var_name, size = var
            parser.symbol_table.declare(var_name, var_type=type_name, is_array=True, size=size)
        else:  # regular variable declaration
            if is_string:
                parser.symbol_table.declare(var, var_type=type_name, is_array=True, size=size) # para CHARACTER * n, declarar como array de caracteres
            else:
                parser.symbol_table.declare(var, var_type=type_name)
    p[0] = ('DECLARE', type_name)


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
         | CHARACTER
         | CHARACTER "*" INT
    """
    if len(p) == 2:
        if p[1] == "CHARACTER":
            p[0] = ('CHARACTER', 1)
        else:
            p[0] = p[1]
    else:
        p[0] = ("CHARACTER", p[3])

def p_parameter_statement(p):
    r"""
    ParameterStatement : PARAMETER "(" ParamAssignList ")"
    """
    params = []
    for var, value in p[3]:
        if not parser.symbol_table.is_constant_expression(value):
            raise SemanticError(f"Value of PARAMETER '{var}' must be a constant expression.")
        inferred_type = parser.symbol_table.get_expr_type(value)
        parser.symbol_table.declare(var, var_type = inferred_type,is_parameter=True, value=value)
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
    elif p[2] == '-':
        p[0] = ('SUB', p[1], p[3])
    elif p[2] == '+':
        p[0] = ('ADD', p[1], p[3])


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
    elif p[2] == '/':
        p[0] = ('DIV', p[1], p[3])
    elif p[2] == '*':
        p[0] = ('MUL', p[1], p[3])

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
    if parser.symbol_table.get_expr_type(p[2]) != 'LOGICAL':
        raise SemanticError("Condition expression in IF statement must be of type LOGICAL.")

    if len(p) == 6:
        p[0] = ('IF', p[2], p[4], None)
    elif len(p) == 8:
        p[0] = ('IF', p[2], p[4], p[6])
    else:
        p[0] = ('IF', p[2], [p[3]], None)


def p_for_statement(p):
    r"""
    DoStatement : DO INT VAR EQUALS Expression "," Expression
                 | DO INT VAR EQUALS Expression "," Expression "," Expression
    """
    var_name = p[3]
    start = p[5]
    end = p[7]
    step = p[9] if len(p) == 10 else None

    parser.symbol_table.set_value(var_name, start) # para garantir que a variável do DO é inicializada com o valor inicial antes de ser usada no corpo do DO
    start_type = parser.symbol_table.get_expr_type(start)
    end_type = parser.symbol_table.get_expr_type(end)
    step_type = parser.symbol_table.get_expr_type(step) if step is not None else  None  # default step tem de ser INT
    
    parser.symbol_table.register_do_label(p[2])
    parser.symbol_table.check_do_loop(var_name, start_type, end_type, step_type)

    if len(p) == 8:
        p[0] = ('DO', p[2], p[3], p[5], p[7], 1)  # default step = 1
    else:
        p[0] = ('DO', p[2], p[3], p[5], p[7], p[9])

def p_return_statement(p):
    r"""
    ReturnStatement : RETURN
    """
    if parser.symbol_table.get_current_scope_type() not in ['FUNCTION', 'SUBROUTINE']:
        raise SemanticError("RETURN statement cannot be used outside of a function or subroutine.")
    
    if not parser.symbol_table.is_return_value_assigned():
        raise SemanticError("Function didn't assign a return value before RETURN statement.")
    
    p[0] = ('RETURN',)

def p_arg_list(p):
    r"""
    ArgList : Expression
            | ArgList "," Expression
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]


def p_formal_param_list(p): # parametros na declaração da função/subrotina
    r"""
    FormalParams : VAR
                 | FormalParams "," VAR
    """
    
    if len(p) == 2:
        parser.symbol_table.declare(p[1], var_type=None, is_formal_param=True) # tipo terá de ser atribuido depois no corpo da função
        p[0] = [p[1]]
    else:
        parser.symbol_table.declare(p[3], var_type=None, is_formal_param=True)
        p[0] = p[1] + [p[3]]

def p_function_header(p):
    r"""
    FunctionHeader : Type FUNCTION VAR
    """
    parser.symbol_table.push_scope(scope_name=p[3], scope_type='FUNCTION', return_type=p[1])
    p[0] = (p[1], p[3])  # tipo de retorno e nome da função


def p_function_declaration(p):
    r"""
    FunctionDeclaration : FunctionHeader "(" FormalParams ")" StatementList END
                        | FunctionHeader "(" ")" StatementList END
    """
    if len(p) == 7:
        params = p[3]
        statement_list = p[5]
    else:
        params = []
        statement_list = p[4]
            
    parser.symbol_table.pop_scope()
    p[0] = ('FUNCTION', p[1][0], p[1][1], params, statement_list)


def p_subroutine_header(p):
    r"""
    SubroutineHeader : SUBROUTINE VAR
    """
    parser.symbol_table.push_scope(scope_name=p[2], scope_type='SUBROUTINE')
    p[0] = p[2]

def p_subroutine_declaration(p):
    r"""
    SubroutineDeclaration : SubroutineHeader StatementList END
                          | SubroutineHeader "(" FormalParams ")" StatementList END
                          | SubroutineHeader "(" ")" StatementList END
    """
    if len(p) == 4:
        params         = []
        statement_list = p[2]
    elif len(p) == 7:
        params         = p[3]
        statement_list = p[5]
    else:
        params         = []
        statement_list = p[4]
 
    sub_name = p[1]
    parser.symbol_table.pop_scope()
    p[0] = ('SUBROUTINE', sub_name, params, statement_list)



def p_call_statement(p):
    r"""
    CallStatement : CALL VAR
                  | CALL VAR "(" ArgList ")"
                  | CALL VAR "(" ")"
    """
    args = []
    if len(p) == 6:
        args = p[4]
    # chamar a subrotina 

    p[0] = ('CALL', p[2], args)
    parser.symbol_table.add_subroutine_call(p[0])

def p_index_or_call(p): # 
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
    parser.symbol_table.register_goto_label(p[2])
    p[0] = ('GOTO', p[2])

def p_stop_statement(p):
    r"""
    StopStatement : STOP
    """
    if len(p) == 2:
        p[0] = ('STOP', None, None)

def p_stop_statement_string(p):
    r"""
    StopStatement : STOP STRING
    """
    p[0] = ('STOP', 'STRING', p[2])

def p_stop_statement_int(p):
    r"""
    StopStatement : STOP INT
    """
    p[0] = ('STOP', 'INT', p[2])


def p_print_statement(p): # print sem args -> linha vazia 
    r"""
    PrintStatement : PRINT Format "," ArgList
                   | PRINT Format
    """
    for arg in (p[4] if len(p) == 5 else []):
        if isinstance(arg, str) and not (arg.startswith('\'') and arg.endswith('\'')):
            if not parser.symbol_table.is_initialized(arg):
                raise SemanticError(f"Variable '{arg}' used in PRINT statement must be declared and initialized before use.")
        elif isinstance(arg, tuple):
            parser.symbol_table.get_expr_type(arg) # também já verifica inicialização/compatibilidade

    if len(p) == 3:
        # PRINT Format
        p[0] = ('PRINT', p[2], [])
    else:
        # PRINT Format , ArgList
        p[0] = ('PRINT', p[2], p[4])

def p_read_arg(p):
    r"""
    ReadArg : VAR
    """
    parser.symbol_table.initialize(p[1]) # para garantir que a variável foi declarada e inicializada antes de ser lida
    p[0] = p[1]

def p_read_arg_index_or_call(p):
    r"""
    ReadArg : IndexOrCall
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
    for var_name in p[4]:
        if isinstance(var_name, str):
            parser.symbol_table.initialize(var_name) # para garantir que as variáveis foram declaradas e inicializadas antes de serem lidas
        elif isinstance(var_name, tuple) and var_name[0] == 'INDEX_OR_CALL':
            array_name = var_name[1]
            parser.symbol_table.initialize(array_name) # para garantir que o array foi declarado e inicializado antes de ser lido
    p[0] = ('READ', p[2], p[4])

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
    name = p[1]
    value = p[3]
    
    parser.symbol_table.set_value(name, value)

    p[0] = ('ASSIGN', p[1], p[3])

def p_assignment_array(p):
    r"""
    Assignment : IndexOrCall EQUALS Expression
    """
    array_name = p[1][1]  # p[1] - ('INDEX_OR_CALL', array_name, index)
    index = p[1][2]
    if len(index) != 1:
        raise SemanticError("Only one index is supported for array access.")
    value = p[3]

    parser.symbol_table.set_value(array_name, value, index[0])

    p[0] = ('ASSIGN', p[1], p[3])

def p_program_header(p):
    r"""
    ProgramHeader : PROGRAM VAR
    """
    parser.symbol_table.push_scope(scope_name=p[2], scope_type='PROGRAM')
    p[0] = p[2]


def p_program(p):
    r"""
    Program : ProgramHeader StatementList END
    """
    parser.symbol_table.pop_scope() 
    p[0] = ('PROGRAM', p[1], p[2])


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

def p_label_statement(p):
    r"""
    Statement : LABEL StatementContent
    """
    parser.symbol_table.declare_label(p[1], p[2])
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
                        | DoStatement
                        | GotoStatement
                        | PrintStatement
                        | ReadStatement
                        | ParameterStatement
                        | Continue
                        | StopStatement
                        | CallStatement
                        | ReturnStatement
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

def p_error(t):
    """Lança erro de parsing com token/linha (ou EOF)."""
    raise ParseError(f"Parse Error: Unexpected token: {t.type if t else '$'} (token value: {t.value}) at line {t.lineno if t else 'EOF'}")

parser = yacc.yacc(start="ProgramUnitList", write_tables=False)
parser.symbol_table = SymbolTable()
parser.quit = False

def get_ast(data, lexer):
    """Faz parse do input e valida GOTOs/DO labels/CALLs pendentes."""
    ast = parser.parse(data, lexer=lexer)

    parser.symbol_table.verify_pending_gotos()
    parser.symbol_table.verify_pending_do_labels()
    parser.symbol_table.verify_pending_calls()

    return ast, parser.symbol_table

def main(args):
    """Executa o parser sobre um ficheiro e imprime o AST (modo debug)."""
    with open(args[1], "r") as f:
        data = f.read()
    try:
        ast = parser.parse(data, lexer=lexer)
        parser.symbol_table.verify_pending_gotos()
        parser.symbol_table.verify_pending_calls()

        print(ast)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main(sys.argv)