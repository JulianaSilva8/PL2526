from errors import SemanticError

class SymbolTable:
    def __init__(self):
        self.symbols = {}

    def add_symbol(self, name, type=None, is_array=False, is_parameter=False):
        if name in self.symbols:
            raise SemanticError(f"Symbol '{name}' already declared.")
        
        self.symbols[name] = {
            'type': type,
            'is_parameter': is_parameter,
            'is_array': is_array
        }

    def update_symbol(self, name, value):
        if name not in self.symbols:
            raise SemanticError(f"Symbol '{name}' not declared.")
        
        self.symbols[name]['value'] = value

    def get_type(self, name):
        if name not in self.symbols:
            raise SemanticError(f"Symbol '{name}' not declared.")
        
        return self.symbols[name]['type']
    
    def get_value(self, name):
        if name not in self.symbols:
            raise SemanticError(f"Symbol '{name}' not declared.")
        
        return self.symbols[name].get('value', None)