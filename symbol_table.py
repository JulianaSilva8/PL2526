from errors import SemanticError

class SymbolTable:
    """
    Symbol table for FORTRAN77 compiler.
    Manages variable declarations, types, initialization status, and unique identifiers.
    Follows the pattern from sexp_plus example.
    """
    
    def __init__(self):
        self.__table = {}
        self.__label_count = 0
        self.__scope_stack = [{}]  # Support for scopes (functions, subroutines)

    def __repr__(self):
        return self.__table.__repr__()

    def symbols(self):
        """Return all declared symbols in current scope."""
        return self.__table.keys()

    def lookup(self, name):
        """
        Look up a symbol in the table.
        Returns symbol information or raises SemanticError if undeclared.
        """
        if name not in self.__table:
            raise SemanticError(f"Undeclared variable: {name}")
        return self.__table[name]

    def declare(self, name, var_type=None, is_array=False, size=None, is_parameter=False, value=None):
        """
        Declare a new identifier with optional type and array information.
        Raises SemanticError if variable is already declared.
        """
        if name in self.__table:
            raise SemanticError(f"Duplicate declaration: {name}")
        
        idx = len(self.__table)
        self.__table[name] = {
            'index': idx,
            'type': var_type,  # INTEGER, REAL, LOGICAL, DOUBLE, CHARACTER
            'initialized': False,
            'is_array': is_array,
            'size': size,
            'is_parameter': is_parameter,
            'value': value  # for parameters and constants
        }

    def initialize(self, name):
        """
        Mark a variable as initialized.
        Raises SemanticError if variable is not declared.
        """
        if name not in self.__table:
            raise SemanticError(f"Undeclared variable: {name}")
        self.__table[name]['initialized'] = True

    def set_value(self, name, value):
        """Update the value of a parameter or constant."""
        if name not in self.__table:
            raise SemanticError(f"Symbol '{name}' not declared.")
        self.__table[name]['value'] = value

    def get_type(self, name):
        """Get the type of a variable."""
        if name not in self.__table:
            raise SemanticError(f"Symbol '{name}' not declared.")
        return self.__table[name]['type']

    def get_value(self, name):
        """Get the value of a parameter or constant."""
        if name not in self.__table:
            raise SemanticError(f"Symbol '{name}' not declared.")
        return self.__table[name].get('value', None)

    def is_initialized(self, name):
        """Check if a variable has been initialized."""
        if name not in self.__table:
            raise SemanticError(f"Symbol '{name}' not declared.")
        return self.__table[name]['initialized']

    def is_array(self, name):
        """Check if a variable is an array."""
        if name not in self.__table:
            raise SemanticError(f"Symbol '{name}' not declared.")
        return self.__table[name]['is_array']

    def get_size(self, name):
        """Get the size of an array variable."""
        if name not in self.__table:
            raise SemanticError(f"Symbol '{name}' not declared.")
        if not self.__table[name]['is_array']:
            raise SemanticError(f"Variable '{name}' is not an array.")
        return self.__table[name]['size']

    def new_label(self):
        """Generate a unique label identifier for control flow."""
        self.__label_count += 1
        return self.__label_count

    def push_scope(self):
        """Push a new scope (for functions and subroutines)."""
        self.__scope_stack.append({})
        self.__table = {}
        self.__label_count = 0

    def pop_scope(self):
        """Pop the current scope and restore parent scope."""
        if len(self.__scope_stack) > 1:
            self.__scope_stack.pop()
            self.__table = self.__scope_stack[-1]
            return True
        return False