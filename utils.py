
# ordem das posições necessarias na stack: retorno (-3), base (-2), expoente (-1)
power_function = """
POWER:
    PUSHI 1   // res
    PUSHL -1   // expoente
    PUSHL -2   // base

POWERLOOP:
    PUSHL 1
    PUSHI 0
    SUP          // expoente > 0
    JZ POWEREND 
    
    // res = res * base
    PUSHL 0
    PUSHL 2
    MUL
    STOREL 0
    
    // expoente = expoente - 1
    PUSHL 1
    PUSHI 1
    SUB
    STOREL 1
    
    JUMP POWERLOOP

POWEREND:
    PUSHL 0
    STOREL -3 // guarda no slot de retorno
    POP 3
    RETURN
"""

power_function_float = """
POWERFLOAT:
    PUSHF 1.0
    PUSHL -1
    PUSHL -2

POWERLOOPF:
    PUSHL 1
    PUSHI 0
    SUP
    JZ POWERENDF
    
    // res = res * base
    PUSHL 0
    PUSHL 2 
    FMUL
    STOREL 0
    
    // expoente = expoente - 1
    PUSHL 1   
    PUSHI 1
    SUB 
    STOREL 1
    
    JUMP POWERLOOPF

POWERENDF:
    PUSHL 0
    STOREL -3
    RETURN
"""