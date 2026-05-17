class ParseError(Exception):
    """Erros de análise sintática (parser)."""
    pass

class SemanticError(Exception):
    """Erros de análise semântica (tabela de símbolos/validações)."""
    pass

class LexError(Exception):
    """Erros de análise léxica (lexer)."""
    pass