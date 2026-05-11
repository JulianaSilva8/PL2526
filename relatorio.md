# Processamento de Linguagens - Compilador Fortran 77 para EWVM
## Trabalho realizado por:
### Juliana Silva A105572
### Sofia Couto A106925
### Soraia Pereira A106806

## Índice
1. [Introdução](#1-introdução)
2. [Estrutura do Projeto](#2-estrutura-do-projeto)
3. [Análise Léxica](#3-análise-léxica)
   - [3.1. Suporte ao formato fixo de Fortran 77](#31-suporte-ao-formato-fixo-de-fortran-77)
   - [3.2. Tipos de literais reconhecidos](#32-tipos-de-literais-reconhecidos)
4. [Análise Sintática e Gramática](#4-análise-sintática-e-gramática)
   - [4.1. Declarações](#41-declarações)
   - [4.2. Expressões](#42-expressões)
   - [4.3. Controlo de fluxo](#43-controlo-de-fluxo)
   - [4.4. Entrada e saída](#44-entrada-e-saída)
5. [Análise Semântica](#5-análise-semântica)
   - [5.1. Verificação de declarações](#51-verificação-de-declarações)
   - [5.2. Verificação de tipos](#52-verificação-de-tipos)
   - [5.3. Verificação de labels e ciclos DO](#53-verificação-de-labels-e-ciclos-do)
   - [5.4. Verificação de funções e subrotinas](#54-verificação-de-funções-e-subrotinas)
6. [Tradução para Código EWVM](#6-tradução-para-código-ewvm)
   - [6.1. Variáveis e memória](#61-variáveis-e-memória)
   - [6.2. Expressões aritméticas](#62-expressões-aritméticas)
   - [6.3. Expressões relacionais e lógicas](#63-expressões-relacionais-e-lógicas)
   - [6.4. Entrada e saída](#64-entrada-e-saída)
   - [6.5. Arrays](#65-arrays)
   - [6.6. Ciclos DO](#66-ciclos-do)
7. [Gramática Implementada](#7-gramática-implementada)
8. [Testes Realizados](#8-testes-realizados)
9. [Dificuldades Encontradas](#9-dificuldades-encontradas)
   - [9.1. Labels e formato fixo](#91-labels-e-formato-fixo)
   - [9.2. Falta de separador explícito entre statements](#92-falta-de-separador-explícito-entre-statements)
   - [9.3. Tipos CHARACTER e STRING](#93-tipos-character-e-string)
   - [9.4. Arrays e indexação](#94-arrays-e-indexação)
   - [9.5. Funções e subrotinas](#95-funções-e-subrotinas)
10. [Limitações Atuais](#10-limitações-atuais)
11. [Instruções de Execução](#11-instruções-de-execução)
12. [Conclusão](#12-conclusão)


## 1. Introdução
Este projeto foi desenvolvido no âmbito da unidade curricular de Processamento de Linguagens e tem como objetivo a construção de um compilador para a linguagem **Fortran 77 Standard**. O compilador implementado recebe como entrada um ficheiro com código Fortran 77 e realiza as várias fases clássicas de compilação: análise léxica, análise sintática, análise semântica e tradução para código máquina da **EWVM**.

No projeto desenvolvido, foi utilizada a biblioteca **PLY** em Python, nomeadamente os módulos `ply.lex` e `ply.yacc`, para implementar o analisador léxico e o analisador sintático.


## 2. Estrutura do Projeto
A implementação foi organizada em vários ficheiros, cada um associado a uma fase ou responsabilidade específica do compilador:

```
.
├── lexer.py          # Analisador léxico
├── parser.py         # Analisador sintático e construção da AST
├── symbol_table.py   # Tabela de símbolos e análise semântica
├── translator.py     # Tradução da AST para código EWVM
├── errors.py         # Classes de erro utilizadas no projeto
├── exemplos/         # Programas Fortran 77 de teste
└── vm/               # Código gerado para a EWVM
```

O ficheiro `errors.py` define exceções próprias, como `ParseError`, `SemanticError` e `SemanticWarning`, permitindo separar erros sintáticos, semânticos e avisos de análise.

A separação em módulos torna o projeto mais organizado: o `lexer.py` identifica os tokens, o `parser.py` valida a gramática e constrói a AST, o `symbol_table.py` gere identificadores, tipos, escopos e validações semânticas, e o `translator.py` transforma a AST em instruções da EWVM.

---

## 3. Análise Léxica
A análise léxica foi implementada no ficheiro `lexer.py`, utilizando a biblioteca `ply.lex`. Esta fase tem como objetivo transformar o código fonte Fortran 77 numa sequência de tokens reconhecíveis pelo parser.

Foram definidas as seguintes palavras reservadas:

```
PROGRAM, END, IF, THEN, ELSE, ENDIF, DO, GOTO,
PRINT, READ, INTEGER, REAL, LOGICAL, CHARACTER,
FUNCTION, SUBROUTINE, CALL, RETURN, PARAMETER, 
STOP, MOD, WRITE
```

Além das palavras reservadas, o lexer reconhece identificadores, números inteiros, números reais, valores lógicos, strings, operadores aritméticos, operadores relacionais e operadores lógicos. No código, os tokens incluem, por exemplo, `LABEL`, `INT`, `NREAL`, `BOOL`, `LT`, `GT`, `LE`, `GE`, `EQ`, `NE`, `VAR`, `DOUBLE`, `AND`, `OR`, `NOT`, `STRING`, `POWER` e `CONCAT`.

### 3.1. Suporte ao formato fixo de Fortran 77 ----------- VER ISTO 
Foi tomada a decisão de considerar parcialmente o formato de colunas fixas do Fortran 77. Em particular, os labels são reconhecidos quando aparecem nas primeiras colunas da linha, com um máximo de cinco dígitos. No lexer, quando é encontrado um número, é verificada a sua posição na linha para decidir se deve ser classificado como `LABEL` ou como `INT`.

Também são ignoradas linhas de comentário iniciadas por `C`, `c` ou `*` na primeira coluna, de acordo com a sintaxe tradicional do Fortran 77.

### 3.2. Tipos de Literais reconhecidos

O compilador reconhece:

```text
Inteiros          → 10, 123, 999
Reais             → 1.5, .89, 1.2E-3, 3.14D0
Lógicos           → .TRUE., .FALSE.
Strings           → 'Ola, Mundo!'
Caracteres        → 'A'
```

Os números reais em notação científica com `D`, comuns em Fortran para dupla precisão, são convertidos para a notação `E` antes de serem transformados em `float`.

---

## 4. Análise Sintática e Gramática

A análise sintática foi implementada no ficheiro `parser.py`, usando `ply.yacc`. Esta fase valida se a sequência de tokens segue a gramática definida para o subconjunto de Fortran 77 suportado pelo compilador.

O parser constrói uma **AST** através de tuplos Python, estando apresentados abaixo alguns:

```python
('DECLARE', tipo)
('PROGRAM', nome, corpo)
('ASSIGN', variavel, expressao)
('IF', condicao, then_body, else_body)
('DO', label, variavel, inicio, fim, passo)
('PRINT', formato, argumentos)
('READ', formato, argumentos)
('CALL', nome, argumentos)
```

A gramática principal aceita uma lista de unidades de programa, onde cada unidade pode ser um `PROGRAM`, uma `FUNCTION` ou uma `SUBROUTINE`. Isto permite processar programas que contém um programa principal seguido de uma função auxiliar.

### 4.1. Declarações

As declarações suportadas incluem tipos simples e arrays:

```fortran
INTEGER N, I, FAT
REAL X
LOGICAL FLAG
CHARACTER TEXTO
CHARACTER*10 NOME
INTEGER NUMS(5)
```

No parser, a regra `Declaration : Type VarList` processa declarações de variáveis simples e arrays, registando-as na tabela de símbolos com o respetivo tipo, tamanho e, no caso de `CHARACTER`, comprimento declarado.

### 4.2. Expressões

O parser define uma hierarquia de expressões para suportar operadores lógicos, relacionais, aritméticos, potência e concatenação. A precedência implementada é:

```text
1. Operadores lógicos: .OR., .AND., .NOT.
2. Operadores relacionais: .LT., .GT., .LE., .GE., .EQ., .NE.
3. Soma e subtração: +, -
4. Multiplicação, divisão e MOD
5. Potência: **
6. Concatenação: //
```

Esta estrutura permite reconhecer expressões como:

```fortran
I .LE. NUM/2 .AND. ISPRIM
VAL = VAL + (REM * POT)
TEXTO = 'OLA' // ' MUNDO'
```

No parser, as expressões são transformadas em nós da AST como `('ADD', left, right)`, `('AND', left, right)`, `('LT', left, right)` ou `('CONCAT', left, right)`.

### 4.3. Controlo de fluxo

Foram implementadas regras para:

```fortran
IF condição THEN
   ...
ELSE
   ...
ENDIF
```

```fortran
DO 10 I = 1, N
   ...
10 CONTINUE
```

```fortran
GOTO 20
```

No caso do `IF`, o parser verifica semanticamente se a condição é do tipo `LOGICAL`. Se a expressão usada como condição não for lógica, é lançado um erro semântico.

No caso do `DO`, são guardados o label de destino, a variável de controlo, o valor inicial, o valor final e o passo. Quando o passo não é indicado, é assumido o valor `1`, tal como é comum em Fortran.

### 4.4. Entrada e saída

Foram implementadas instruções de entrada e saída:

```fortran
PRINT *, 'Ola, Mundo!'
PRINT *, 'BASE ', BASE, ': ', RESULT
READ *, N
WRITE (*,*) 'Texto'
```

O `PRINT` aceita um formato e uma lista opcional de argumentos. Quando não existem argumentos, é interpretado como impressão de uma linha vazia. O `READ` recebe uma lista de variáveis ou posições de array onde os valores lidos serão armazenados.

O `WRITE` também foi adicionado ao parser com suporte a um par de controlo, como `WRITE(*,*)`, embora o comportamento no tradutor tenha sido aproximado ao de `PRINT`.

---

## 5. Análise Semântica

A análise semântica é feita principalmente através da classe `SymbolTable`, definida em `symbol_table.py`. Esta estrutura mantém informação sobre variáveis, arrays, parâmetros, labels, funções, subrotinas e escopos.

Cada símbolo guarda informação como:

```text
index             posição na memória
type              tipo da variável
initialized       indica se já foi inicializada
is_array          indica se é array
size              tamanho do array
char_len          comprimento de CHARACTER
is_parameter      indica se é constante PARAMETER
is_formal_param   indica se é parâmetro formal
is_label          indica se é label
value             valor associado, quando aplicável
```

A tabela de símbolos suporta múltiplos escopos, nomeadamente o escopo global, escopos de programas, funções e subrotinas. Esta organização é importante porque funções e subrotinas têm os seus próprios parâmetros e variáveis locais.

### 5.1. Verificação de declarações

Sempre que uma variável é usada, é verificado se foi previamente declarada. O compilador também deteta declarações duplicadas, uso de variáveis não inicializadas e tentativas de atribuir valores a constantes definidas por `PARAMETER`.

Exemplo de erro semântico possível:

```text
Undeclared variable: X
Duplicate declaration: N
Cannot assign a value to parameter 'MAX' after declaration.
```

### 5.2. Verificação de tipos

A função `get_expr_type` determina o tipo de uma expressão. Esta função é usada para validar atribuições, condições de `IF`, expressões lógicas, operações relacionais, concatenação de strings e chamadas a funções.

Por exemplo:

```fortran
LOGICAL FLAG
FLAG = .TRUE.
IF (FLAG) THEN
   PRINT *, 'OK'
ENDIF
```

é válido, mas:

```fortran
INTEGER X
IF (X) THEN
   PRINT *, 'ERRO'
ENDIF
```

deve originar erro, porque a condição de um `IF` tem de ser lógica.

O código também valida compatibilidade entre tipos numéricos, permitindo algumas promoções entre `INTEGER`, `REAL` e `DOUBLE`, e aceita compatibilidade entre `STRING` e `CHARACTER` em atribuições ou concatenações.

### 5.3. Verificação de labels e ciclos DO

Os labels usados por `GOTO` e `DO` são registados para verificação posterior. No final da análise, o compilador verifica se todos os saltos apontam para labels existentes. Também é verificado se a variável de controlo do ciclo `DO` é inteira e se os limites do ciclo são numéricos.

Esta verificação é importante para exemplos como:

```fortran
DO 10 I = 1, N
   FAT = FAT * I
10 CONTINUE
```

Neste caso, o label `10` deve existir e estar associado a uma instrução válida.

### 5.4. Verificação de funções e subrotinas

O compilador suporta a declaração e chamada de `FUNCTION` e `SUBROUTINE`. As chamadas são verificadas quanto à existência da função/subrotina, ao número de argumentos e aos respetivos tipos.

Quando uma função é chamada antes de ser totalmente conhecida, a verificação é adiada e guardada numa lista de chamadas pendentes. No final da análise, essas chamadas são validadas através de `verify_pending_calls`.

---

## 6. Tradução para Código EWVM

A tradução para código máquina da EWVM é feita no ficheiro `translator.py`. Esta fase percorre a AST e gera instruções correspondentes para a máquina virtual.

O tradutor usa métodos específicos para cada tipo de nó, como:

```text
gen_program
gen_assign
gen_print
gen_read
gen_if
gen_do
gen_goto
gen_call
gen_function
gen_subroutine
gen_arithmetic
gen_relational
gen_logical
gen_index_or_call
```

A função principal `translate` faz o despacho com base no primeiro elemento do tuplo da AST. Por exemplo, se o nó começar por `'ASSIGN'`, é chamada a função `gen_assign`; se começar por `'PRINT'`, é chamada `gen_print`.

### 6.1. Variáveis e memória

Cada variável recebe um índice na tabela de símbolos. Durante a tradução, esse índice é usado para gerar instruções como:

```text
PUSHI valor
PUSHF valor
PUSHS "texto"
STOREG índice
PUSHG índice
```

Por exemplo, a atribuição:

```fortran
X = 10
```

pode ser traduzida para algo semelhante a:

```text
PUSHI 10
STOREG <índice de X>
```

Para variáveis reais, é usado `PUSHF`; para strings e caracteres, é usado `PUSHS`; para booleanos, são usados inteiros `1` e `0`.

### 6.2. Expressões aritméticas

As expressões aritméticas são traduzidas empilhando primeiro os operandos e depois aplicando a instrução correspondente:

```fortran
SOMA = SOMA + NUMS(I)
```

pode gerar uma sequência onde os valores são carregados para a stack e depois é aplicada a instrução `ADD`.

O tradutor suporta operadores como:

```text
ADD, SUB, MUL, DIV, MOD, POW
```

### 6.3. Expressões relacionais e lógicas

As expressões relacionais são traduzidas para instruções da EWVM como:

```text
INF      <
SUP      >
INFEQ    <=
SUPEQ    >=
EQUAL    ==
NOT      negação
```

No caso de `.NE.`, o tradutor gera primeiro `EQUAL` e depois `NOT`, representando a operação “diferente de”.

As expressões lógicas `.AND.` e `.OR.` são traduzidas para as instruções `AND` e `OR`.

### 6.4. Entrada e saída

A instrução `PRINT` é traduzida através de instruções de escrita da EWVM:

```text
WRITEI   escrita de inteiros
WRITEF   escrita de reais
WRITES   escrita de strings/caracteres
```

No caso de literais string, as aspas vindas do parser são removidas antes da geração do `PUSHS`, para que a string seja corretamente impressa. O tradutor também acrescenta uma quebra de linha no fim de cada `PRINT`.

Exemplo:

```fortran
PRINT *, 'A soma dos numeros e: ', SOMA
```

pode gerar:

```text
PUSHS "A soma dos numeros e: "
WRITES
PUSHG <índice de SOMA>
WRITEI
PUSHS "\n"
WRITES
```

O `READ` usa a instrução `READ`, seguida de conversões como `ATOI` ou `ATOF`, dependendo do tipo da variável lida. Para arrays, é calculado o endereço da posição pretendida e usado `STOREN`.

### 6.5. Arrays

Os arrays em Fortran começam no índice 1. Como a representação em memória da EWVM é tratada com base em endereços, o tradutor ajusta o índice subtraindo 1:

```fortran
NUMS(I)
```

é tratado como:

```text
endereço_base(NUMS) + (I - 1)
```

No tradutor, este comportamento aparece nas funções que tratam acessos a arrays e leituras para posições de array.

### 6.6. Ciclos DO

O ciclo `DO` é traduzido através de labels internos gerados automaticamente. O tradutor cria uma label de início e uma label de fim, inicializa a variável de controlo, verifica a condição de continuação e gera um salto condicional para sair do ciclo.

Exemplo Fortran:

```fortran
DO 10 I = 1, N
   FAT = FAT * I
10 CONTINUE
```

Estrutura conceptual gerada:

```text
PUSHI 1
STOREG I

DO_10_START:
PUSHG I
PUSHG N
INFEQ
JZ DO_10_END

...
incremento de I
JUMP DO_10_START

DO_10_END:
```

---

## 7. Gramática Implementada

Nesta secção do relatório é apresentada uma versão resumida da gramática implementada, focando as regras principais do parser.

```text
ProgramUnitList → ProgramUnitList ProgramUnit
                | ProgramUnit

ProgramUnit → Program
            | FunctionDeclaration
            | SubroutineDeclaration

Program → PROGRAM VAR StatementList END

StatementList → Statement
              | StatementList Statement

Statement → StatementContent
          | LABEL StatementContent

StatementContent → Declaration
                 | Assignment
                 | IfStatement
                 | DoStatement
                 | GotoStatement
                 | PrintStatement
                 | ReadStatement
                 | WriteStatement
                 | ParameterStatement
                 | Continue
                 | StopStatement
                 | CallStatement
                 | ReturnStatement

Declaration → Type VarList

Type → INTEGER
     | REAL
     | LOGICAL
     | DOUBLE
     | CHARACTER
     | CHARACTER * INT

Assignment → VAR = Expression

IfStatement → IF Expression THEN StatementList ENDIF
            | IF Expression THEN StatementList ELSE StatementList ENDIF
            | IF Expression StatementContent

DoStatement → DO INT VAR = Expression , Expression
            | DO INT VAR = Expression , Expression , Expression

GotoStatement → GOTO INT

PrintStatement → PRINT Format , ArgList
               | PRINT Format

ReadStatement → READ Format , ReadArgList

FunctionDeclaration → Type FUNCTION VAR ( FormalParams ) StatementList END

SubroutineDeclaration → SUBROUTINE VAR StatementList END
                      | SUBROUTINE VAR ( FormalParams ) StatementList END
```

A gramática produz uma AST simples baseada em tuplos Python, o que simplifica a passagem para a fase de tradução.

---

## 8. Testes Realizados

Os testes foram baseados nos exemplos sugeridos no enunciado, nomeadamente:

| Teste | Funcionalidade testada | Estado |
|---|---|---|
| `ex1.f` | `PROGRAM`, `PRINT`, string literal | Funciona / A validar |
| `ex2.f` | `READ`, `DO`, `CONTINUE`, multiplicação | Funciona / A validar |
| `ex3.f` | `IF`, `.AND.`, `MOD`, `GOTO`, booleanos | Funciona / A validar |
| `ex4.f` | Arrays, leitura para array, soma acumulada | Funciona / Parcial |
| `ex5.f` | `FUNCTION`, chamada de função, `RETURN` | Parcial / Em desenvolvimento |
| `ex8Sofia.f` | `CHARACTER`, `WRITE`, concatenação, lógica | Parcial / Em desenvolvimento |

O enunciado recomenda a criação de programas Fortran de teste e respetivos ficheiros com código VM gerado, para validar a correção do compilador.

Para cada programa de teste foi executado o compilador, analisada a AST produzida e comparado o comportamento do código EWVM gerado com o resultado esperado. Os testes permitiram validar progressivamente cada construção da linguagem, começando por programas simples com `PRINT` e evoluindo para exemplos com ciclos, arrays, funções e expressões compostas.

---

## 9. Dificuldades Encontradas

Durante o desenvolvimento surgiram várias dificuldades relacionadas com a aproximação entre a sintaxe original de Fortran 77 e a representação necessária para a EWVM.

### 9.1. Labels e formato fixo

Uma dificuldade inicial foi distinguir números comuns de labels. Em Fortran 77, os labels aparecem nas primeiras colunas da linha, enquanto números usados em expressões podem surgir em qualquer posição. Para resolver este problema, o lexer verifica a coluna onde o número aparece e classifica-o como `LABEL` apenas quando está nas primeiras cinco colunas.

### 9.2. Falta de separador explícito entre statements

Outra dificuldade foi o facto de o parser não usar um token explícito de fim de linha. Como consequência, algumas regras podem tornar-se ambíguas, especialmente em instruções como `WRITE`, que podem ter argumentos opcionais. Isto pode originar conflitos `shift/reduce`, porque o parser tem dificuldade em decidir se o token seguinte pertence ao statement atual ou se inicia um novo statement.

Uma possível melhoria futura seria introduzir um token de fim de linha ou pré-processar o código Fortran para normalizar as linhas antes da análise sintática.

### 9.3. Tipos CHARACTER e STRING

O tratamento de `CHARACTER` exigiu uma distinção entre caracteres de comprimento 1 e strings maiores. No lexer, as strings mantêm as aspas para permitir distinguir literais de identificadores durante a análise semântica.

Na análise semântica, foi necessário permitir compatibilidade entre `CHARACTER` e `STRING`, especialmente em atribuições e concatenações. No tradutor, por outro lado, foi necessário remover as aspas antes de gerar instruções `PUSHS`.

### 9.4. Arrays e indexação

Fortran usa arrays com índice inicial 1, enquanto a implementação em memória da EWVM exige cálculo de endereços. Por isso, em acessos como `NUMS(I)`, foi necessário converter o índice para base 0, usando a expressão `I - 1`.

### 9.5. Funções e subrotinas

O suporte a `FUNCTION` e `SUBROUTINE` exigiu a criação de escopos próprios, verificação de parâmetros formais e validação de chamadas. Como algumas funções podem ser chamadas antes de serem completamente processadas, foi necessário guardar chamadas pendentes e verificá-las no final da análise.

---

## 10. Limitações Atuais

A versão atual do compilador já reconhece várias construções importantes de Fortran 77, mas ainda apresenta algumas limitações:

- O suporte a `WRITE` ainda é aproximado ao comportamento de `PRINT`.
- `FORMAT` não é totalmente interpretado; por enquanto é sobretudo reconhecido sintaticamente.
- O tratamento de continuação de linhas ainda pode ser melhorado.
- Algumas instruções de tradução de funções/subrotinas ainda precisam de validação completa.
- O fecho de ciclos `DO` através de `CONTINUE` pode exigir lógica adicional no tradutor.
- A gestão de arrays em atribuições ainda pode ser melhorada.
- A otimização de código ainda não foi implementada de forma significativa.

Apesar destas limitações, a estrutura do compilador permite evoluir facilmente cada uma das fases, uma vez que a análise léxica, análise sintática, análise semântica e tradução se encontram separadas em módulos distintos.

---

## 11. Instruções de Execução

Para executar o compilador, é necessário ter Python instalado e instalar a biblioteca PLY:

```bash
pip install ply
```

Para testar apenas o lexer:

```bash
python3 lexer.py exemplos/ex1.f
```

Para executar o parser e obter a AST:

```bash
python3 parser.py exemplos/ex1.f
```

Quando a fase de tradução estiver ligada ao parser, o comando esperado poderá ser:

```bash
python3 parser.py exemplos/ex1.f > exemplos/ex1.vm
```

ou, caso exista um ficheiro principal próprio:

```bash
python3 compiler.py exemplos/ex1.f exemplos/ex1.vm
```

Depois, o código gerado pode ser executado na EWVM com o comando definido pela máquina virtual disponibilizada pela unidade curricular, por exemplo:

```bash
java -jar ewvm.jar exemplos/ex1.vm
```

Este último comando deve ser adaptado ao nome real da VM utilizada.

---

## 12. Conclusão

Neste projeto foi desenvolvido um compilador parcial para Fortran 77, capaz de realizar análise léxica, análise sintática, análise semântica e geração de código para a EWVM. A implementação foi feita em Python com recurso à biblioteca PLY, seguindo uma arquitetura modular dividida em lexer, parser, tabela de símbolos e tradutor.

O compilador suporta declarações de variáveis, arrays, tipos básicos, expressões aritméticas, lógicas e relacionais, estruturas condicionais, ciclos `DO`, saltos com `GOTO`, operações de entrada/saída e suporte inicial a funções e subrotinas. A tabela de símbolos permite validar declarações, inicializações, tipos, labels e chamadas a subprogramas, contribuindo para uma análise semântica mais robusta.

Embora existam ainda limitações, nomeadamente no suporte completo a `FORMAT`, `WRITE`, continuação de linhas e algumas partes da tradução de subprogramas, a base implementada cumpre a estrutura essencial de um compilador e permite a evolução incremental para suportar mais funcionalidades da linguagem Fortran 77.
