from translator import Translator
from parser import * 
from lexer import *
from errors import LexError, ParseError, SemanticError
from symbol_table import SymbolTable
import sys

# main
def main(args):
    with open(args[1], "r") as f:
        data = f.read()
    try: 
        check_indentation(data)
        lexer = lex.lex()
        ast, symbol_table = get_ast(data, lexer)
        translator = Translator(symbol_table)
        code, aux = translator.translate(ast)
        
        with open('output.txt', "w") as f:
            for line in code:
                f.write(line + "\n")
            f.write(aux)
        print("Successfully translated to output.txt")
    except LexError as e:
        print(f"Erro de análise léxica: {e}")
    except ParseError as e:
        print(f"Erro de análise sintática: {e}")
    except SemanticError as e:
        print(f"Erro de análise semântica: {e}")
    
    
if __name__ == "__main__":
    main(sys.argv)