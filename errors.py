class ParseError(Exception):
    """Parse-time errors from the parser."""
    pass

class SemanticError(Exception):
    """Semantic errors raised by semantic analysis and symbol table."""
    pass

class LexError(Exception):
    pass