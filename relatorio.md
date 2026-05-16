# Processamento de Linguagens - Compilador Fortran 77 para EWVM

## Trabalho realizado por:

### Juliana Silva A105572

### Sofia Couto A106925

### Soraia Pereira A106806

## Índice

1. [Introdução](#1-introdução)
2. [Estrutura do Projeto](#2-estrutura-do-projeto)
3. [Análise Léxica](#3-análise-léxica)
   - [3.1. Palavras Reservadas e Tokens](#31-palavras-reservadas-e-tokens)
4. [Análise Sintática e Gramática](#4-análise-sintática-e-gramática)
   - [4.1. Declarações e Tipos](#41-declarações-e-tipos)
   - [4.2. Hierarquia de Expressões](#42-hierarquia-de-expressões)
   - [4.3. Construção da Árvore de Sintaxe Abstrata (AST)](#43-construção-da-árvore-de-sintaxe-abstrata-ast)
5. [Análise Semântica](#5-análise-semântica)                                                 // SORAIA
   - [5.1. Verificação de declarações](#51-verificação-de-declarações)
   - [5.2. Verificação de tipos](#52-verificação-de-tipos)
   - [5.3. Verificação de labels e ciclos DO](#53-verificação-de-labels-e-ciclos-do)
   - [5.4. Verificação de funções e subrotinas](#54-verificação-de-funções-e-subrotinas)
6. [Tradução para Código EWVM](#6-tradução-para-código-ewvm)
7. [Testes Realizados](#8-testes-realizados)                                                 // SORAIA
8. [Dificuldades Encontradas e Limitações Atuais](#8-dificuldades-encontradas-e-limitações-atuais)
9. [Otimizações implementadas](#9-otimizações-implementadas)
   - [9.1. Constant Folding](#91-constant-folding)
   - [9.2. Eliminação de Código Morto](#92-eliminação-de-código-morto)
   - [9.3. Remoção de Ciclos Mortos](#93-remoção-de-ciclos-mortos)
   - [9.4. Eliminação de Dupla Negação](#94-eliminação-de-dupla-negação)
10. [Instruções de Execução](#11-instruções-de-execução)
11. [Conclusão](#12-conclusão)

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

A análise léxica foi implementada com a biblioteca `PLY` que gera um analisador léxico a partir de expressoes regulares. O lexer percorre o código-fonte em  Fortran77 e produz sequências de tokens.

É importante mencionar que antes de iniciar a tokenização, é feita uma validação da identação de código através da função `check_identation()`. Esta função é responsável por verificar que o código segue as regras do Fortran77:
   - Comentários: Identifica linhas que comecem em `C`, `c` ou `*` e ignora-as;
   - Labels: entre as colunas 1 e 5 só são aceites inteiros, que correspondem ao token `LABEL`. Se a função detetar que nesse espaço estão caracteres que nao sejam digitos lança um `LexError`.

### 3.1. Palavras Reservadas e Tokens
Os tokens são todas as unidades léxicas que o lexer pode produzir. 
Neste projeto inclui: 
   - Labels numéricas: `LABEL`
   - Literais inteiros e reais: `INT, NREAL`
   - Booleanos: `BOOL`
   - Strings: `STRING`
   - Identificadores de variáveis: `VAR`
   - Operadores aritméticos, relacionais e lógicos: `OPADDSUB, OPDIV, POWER, CONCAT, LT, GT, LE, GE, EQ, NE, AND, OR, NOT`
   - Operador de atribuição: `EQUALS`
   - Linhas de continuação: `CONTINUATION`
   - Literais de caracteres únicos: `(`, `)`, `,`, `*`, `'`

Espaços e tabulações são ignorados.

As palavras reservadas são um subconjunto dos tokens que, como o nome indica, têm um significado fixo na linguagem que não pode ser usado para outros fins, como nomear variáveis. Estas palavras incluem:
   - Instruções de controlo de fluxo: `IF, THEN, ELSE, ENDIF, DO, GOTO, CONTINUE, RETURN, STOP`
   - Declarações de unidades de programa: `PROGRAM, END, FUNCTION, SUBROUTINE, CALL`
   - Declaração de Atributos ou Constantes: `INTEGER, REAL, LOGICAL, CHARACTER, PARAMETER`
   - Instruções de entrada/saída: `PRINT, READ, WRITE`
   - Funções Intrínsecas: `MOD`

Quando o lexer lê  um identificador, verifica se pertence ao conjunto de palavras reservadas e, caso detete que pertence, promove o seu tipo para o token correspondente.

Se algum token não for reconhecido, é lançada um ```LexError``` com a linha em que ocorreu.

---

## 4. Análise Sintática e Gramática

A análise sintática é a segunda fase do processo de compilação, responsável por verificar se a sequência de tokens produzida pelo analisador léxico está organizada de acordo com as regras gramaticais da linguagem. Neste projeto, o analisador sintático foi implementado em Python com recurso à biblioteca **PLY (Python Lex-Yacc)**, que gera um parser LALR(1) a partir das regras de produção definidas.


### 4.1. Declarações e Tipos

O ponto de arranque é o `ProgramUnitList`, que representa o ficheiro Fortran composto por uma ou mais unidades de programa, onde cada uma pode ser um `PROGRAM`, uma `FUNCTION` ou uma `SUBROUTINE`. Cada unidade começa com um cabeçalho que cria um novo âmbito na tabela de símbolos, contém uma lista de instruções e termina com `END`.

```
ProgramUnitList : ProgramUnit | ProgramUnitList ProgramUnit
ProgramUnit     : Program | FunctionDeclaration | SubroutineDeclaration
Program         : ProgramHeader StatementList END
ProgramHeader   : PROGRAM VAR
```

São suportados os tipos `INTEGER`, `REAL`, `LOGICAL` e `CHARACTER` para declaração de variáveis, que podem ser simples ou arrays unidimensionais com declaração de tamanho. Para além disso, também é suportado declaração de constantes através da palavra reservada `PARAMETER`, sendo o seu valor obrigatoriamente uma expressão verificável em tempo de compilação.


### 4.2. Hierarquia de Expressões 
As expressões seguem uma hierarquia, representada na tabela abaixo, onde categorias com nível mais alto têm precedência sob as de níveis mais baixos:

| Nível | Categoria             | Operadores                          |
|-------|-----------------------|-------------------------------------|
| 1     | Lógico                | `.OR.`                              |
| 2     | Lógico                | `.AND.`                             |
| 3     | Negação lógica        | `.NOT.`                             |
| 4     | Relacional            | `.LT.` `.GT.` `.LE.` `.GE.` `.EQ.` `.NE.` |
| 5     | Aditivo               | `+`, `-`                            |
| 6     | Multiplicativo        | `*`, `/`, `MOD(...)`                |
| 7     | Potência              | `**`                                |
| 8     | Concatenação          | `//`                                |
| 9     | Átomo                 | variáveis, literais, chamadas       |

Esta hierarquia é a responsável por garantir, entre outras, que somas não são efetuadas antes de multiplicações na mesma expressão e está expressa na gramática através de não-terminais encadeados. Assim não há a necessidade de declarações explícitas de precedência:

```
Expression          : LogicalTerm | Expression OR LogicalTerm
LogicalTerm         : LogicalFactor | LogicalTerm AND LogicalFactor
LogicalFactor       : NOT LogicalFactor | NonLogicalExpression
NonLogicalExpression: AdditiveExpression | AdditiveExpression RelationalOp AdditiveExpression
AdditiveExpression  : Term | AdditiveExpression OPADDSUB Term
Term                : PowerExpression | Term OPDIV PowerExpression
                    | Term "*" PowerExpression | MOD "(" Term "," PowerExpression ")"
PowerExpression     : ConcatenationExpression | PowerExpression POWER ConcatenationExpression
ConcatenationExpression : ExpressionElement | ConcatenationExpression CONCAT ExpressionElement
ExpressionElement   : VAR | IndexOrCall | INT | NREAL | BOOL | STRING | "(" Expression ")"
```

É importante notar que o `IndexOrCall` é ambíguo a nível sintático já que tanto o acesso a arrays como a chamada de funções partilham a sintaxe `VAR(args)`. Assim, a sua distinção é feita na fase de análise semântica, onde a tabela de símbolos determina se o identificador corresponde a um array ou a uma função.


### 4.3. Construção da Árvore de Sintaxe Abstrata (AST)
À medida que as regras são validadas, o parser constrói nós em formato de tuplos, gerando uma árvores que representa o programa de forma estruturada. Para uma melhor explicação, foi gerado o exemplo abaixo:

O código 
```
IF (A .LT. B) THEN
          X = 10
      ELSE
          X = 20
      ENDIF 
```
gera a seguinte AST:
```
(
    'IF', 
    ('LT', 'A', 'B'),           
    [('ASSIGN', 'X', 10)],      
    [('ASSIGN', 'X', 20)]       
)
```

---

## 5. Análise Semântica

A análide semântica foi implementada principalmente através da classe `SymbolTable`, que guarda duas estruturas de dados principais: uma lista de escopos e uma tabela de símbolos. Os símbolos guardados como na tabela de símbolos incluem variáveis de tipos simples, arrays, parâmetros (as constantes definidas por `PARAMETER`), labels, parâmetros formais de funções e subrotinas e os valores de retorno de funções. A estrutura da tabela de símbolos corresponde a um dicionário onde as chaves são os nomes dos símbolos e os valores são objetos que guardam informação detalhada sobre cada símbolo. Esta informação encontra-se representada sobre a forma de um dicionário com os seguintes valores chave:

<table>
  <tr>
    <td>index</td>
    <td>Índice atribuído à variável sequencialmente consoante o parsing na análise sintática.</td>
  </tr>
   <tr>
      <td>type</td>
      <td>Tipo da variável (INTEGER, REAL, LOGICAL, CHARACTER, etc.).</td>
   </tr>
   <tr>
      <td>initialized</td>
      <td>Indica se a variável já foi inicializada.</td>
   </tr>
   <tr>
      <td>is_array</td>
      <td>Indica se a variável é um array.</td>
   </tr>
   <tr>
      <td>size</td>
      <td>Tamanho do array, caso seja um array.</td>
   </tr>
   <tr>
      <td>is_parameter</td>
      <td>Indica se a variável é um parâmetro constante definido por PARAMETER.</td>
   </tr>
   <tr>
      <td>is_formal_param</td>
      <td>Indica se a variável é um parâmetro formal de uma função ou subrotina.</td>
   </tr>
   <tr>
      <td>is_return_value</td>
      <td>Indica se a variável é o valor de retorno de uma função.</td>
   </tr>
   <tr>
      <td>is_label</td>
      <td>Indica se o símbolo é uma label.</td>
   </tr>
   <tr>
      <td>value</td>
      <td>Valor associado ao símbolo, quando aplicável (quando valor é uma constante e não calculado em tempo de execução).</td>
   </tr> 
</table>


A lista de escopos está representada por duas estruturas: uma "stack" com os nomes dos escopos e um dicionário que mapeia cada nome de escopo para um dicionário contendo as seguintes informações:

<table>
  <tr>
    <td>name</td>
    <td>Nome do escopo</td>
  </tr>
   <tr>
      <td>vars</td>
      <td>Estrutura da tabela de símbolos associada ao escopo</td>
   </tr>
   <tr>
      <td>Prev</td>
      <td>Nome do escopo anterior</td>
   </tr>
   <tr>
      <td>type</td>
      <td>Tipo do escopo (programa, função, subrotina)</td>
   </tr>
   <tr>
      <td>return_type</td>
      <td>Tipo de retorno caso o escopo seja uma função</td>
   </tr>
   <tr>
      <td>return_value_assigned</td>
      <td>Indica se o valor de retorno da função já foi atribuído em algum ponto do código</td>
   </tr>
   <tr>
      <td>return_address</td>
      <td>Usado para as funções na fase de tradução</td>
</table>

O escopo global corresponde ao escopo usado para o programa principal. Quando se entra numa regra de produção de uma unidade de programa, mais especificamente nas regras de produção das headers para as funções e subrotinas, é chamada a função `push_scope` que guarda a tabela de símbolos do escopo anterior na lista de escopos e cria uma tabela nova vazia para o novo escopo. Quando se sai da regra de produção, é chamada a função `pop_scope` que guarda a tabela de símbolos no dicionário do escopo atual na lista de escopos e atualiza para o escopo anterior. Embora a implementação de escopos tenha sido feita sobre a forma de uma stack, esta estrutura acabou por não ser tão útil como esperado, uma vez que o Fortran 77 não tem suporte a blocos aninhados.

Esta classe implementa várias funções que permitem fazer a verificação semântica do código, levantando uma exceção `SemanticError` quando é detetado um erro semântico. Estas funções são chamadas nas funções de produção do parser, o que permite fazer a verificação semântica durante a construção da AST. Nas verificações semânticas implementadas recorreu-se ao uso da função auxiliar `get_expr_type` que, dado um nodo da AST, usa recursividade para determinar o tipo de uma expressão, usando tipagem automática? para valores constantes e recorrenddo à tabela de símbolos para variáveis. A própria função levanta erros semânticos quando deteta incompatibilidades de tipos em operações ou uso de variáveis não declaradas ou inicializadas.


### 5.1. Verificação de declarações e acesso a variáveis

Sempre que uma variável é declarada é verificada se já existe no mesmo escopo uma variável com o mesmo nome ou se existe um escopo com o mesmo nome. O mesmo acontece para as labels e escopos. Quando uma variável é usada, é verificado se foi previamente declarada. O compilador também deteta o acesso a variáveis não inicializadas e tentativas de atribuir valores a constantes declaradas através do comadno `PARAMETER`.


### 5.2. Compatibilidade de tipos

Em todas as expressões, o compilador verifica a compatibilidade de tipos entre variáveis e literais, assim como a compatibilidade de tipos com as operações usadas. Como mencionado anteriormente, isto é feito através da função `get_expr_type`, que determina o tipo de uma expressão e levanta erros semânticos quando deteta incompatibilidades. Também é verificada a compatibilidade de tipos na atribuição de variáveis, em certas construções como o `IF`, onde a condição tem de ser do tipo `LOGICAL` e no acesso a arrays, onde o índice tem de ser do tipo `INTEGER` e, em casos em que pode ser obtido o valor do indíce em tempo de compilação, tem de estar dentro dos limites do array.

### 5.3. Validação de instruções de salto

Os labels usados por `GOTO` e `DO` são registados para verificação posterior. No final da análise, o compilador verifica se todos os saltos apontam para labels existentes. Também é verificado se a variável de controlo do ciclo `DO` é inteira e se os limites do ciclo são numéricos.

### 5.4. Verificação de funções e subrotinas
Todas as funções e subrotinas têm de redeclarar os seus parâmetros formais dentro do seu escopo, para que seja possível obter os seus tipos. No fim da análise, é verificado se todas as funções e subrotinas chamadas foram declaradas, e se os parâmetros usados nas chamadas são compatíveis em número e tipo com os parâmetros formais declarados. No caso das funções, é verificado se em algum ponto do código é atribuído um valor de retorno à função antes do comando `RETURN`.

---

## 6. Tradução para Código EWVM

A tradução para código máquina da EWVM é feita no ficheiro `translator.py` e corresponde à fase final do compilador.
Depois da análise léxica, sintática e semântica, é criado um objeto Translator com a symbol_table. Este objeto percorre a AST gerada pelo parser e a transforma cada nó numa lista de instruções em código máruina, que no fim é gravada no ficheiro `output.txt`. 

Dentro do `translator.py`, a classe Translator percorre cada unidade do programa, como PROGRAM, FUNCTION ou SUBROUTINE, chamando funções específicas como gen_program, gen_function e gen_subroutine. Depois, para cada nó da AST, identifica o seu tipo, por exemplo ASSIGN, IF, DO, PRINT, CALL ou operações aritméticas, e encaminha-o para o respetivo gerador de código.

Durante este processo, o translator consulta a tabela de símbolos para obter informação sobre variáveis, tipos, índices e escopos. Também aloca memória para as variáveis e traduz expressões e instruções de Fortran77 para comandos da EWVM, como PUSHI, PUSHG, STOREG, JUMP, CALL, WRITEI, etc

Assim, o translator recebe a estrutura do programa já validada e produz o código máquina correspondente ao original em Fortran77.

---

## 7. Testes Realizados

Os testes foram baseados nos exemplos sugeridos no enunciado, nomeadamente:

| Teste        | Funcionalidade testada                     | Estado                       |
| ------------ | ------------------------------------------ | ---------------------------- |
| `ex1.f`      | `PROGRAM`, `PRINT`, string literal         | Funciona / A validar         |
| `ex2.f`      | `READ`, `DO`, `CONTINUE`, multiplicação    | Funciona / A validar         |
| `ex3.f`      | `IF`, `.AND.`, `MOD`, `GOTO`, booleanos    | Funciona / A validar         |
| `ex4.f`      | Arrays, leitura para array, soma acumulada | Funciona / Parcial           |
| `ex5.f`      | `FUNCTION`, chamada de função, `RETURN`    | Parcial / Em desenvolvimento |
| `ex8Sofia.f` | `CHARACTER`, `WRITE`, concatenação, lógica | Parcial / Em desenvolvimento |

O enunciado recomenda a criação de programas Fortran de teste e respetivos ficheiros com código VM gerado, para validar a correção do compilador.

Para cada programa de teste foi executado o compilador, analisada a AST produzida e comparado o comportamento do código EWVM gerado com o resultado esperado. Os testes permitiram validar progressivamente cada construção da linguagem, começando por programas simples com `PRINT` e evoluindo para exemplos com ciclos, arrays, funções e expressões compostas.

---

## 8. Dificuldades Encontradas e Limitações Atuais

Durante o desenvolvimento do compilador, surgiram várias dificuldades principalmente devido às diferenças entre a linguagem Fortran77 e o código máquina da EWVM.

Uma parte desafiante foi a implementação das labels. Em Fortran77, as labels são usadas em instruções como GOTO e nos ciclos DO, podendo aparecer no início de linhas e estar associadas ou não a instruções como CONTINUE. Foi necessário garantir que estas labels eram reconhecidas corretamente, guardadas na tabela de símbolos e depois traduzidas para labels válidas em código EWVM.

Outra dificuldade importante foi a implementação de funções e subrotinas. Foi necessário tratar diferentes escopos, parâmetros formais, chamadas com argumentos, valores de retorno e a passagem correta de informação através da pilha. No caso das funções, a análise semântica verifica se em algum ponto é atribuído um valor de retorno à função antes do RETURN. No entanto, esta verificação ainda é limitada, porque não analisa todos os caminhos possíveis de execução. 

A implementação de arrays também trouxe dificultades sobretudo devido à diferença de indexação entre Fortran77 e a EWVM. Em Fortran77, os arrays começam no índice 1, enquanto na EWVM a indexação usada na memória começa em 0. Por isso, sempre que é feito um acesso a um array, foi necessário gerar código extra para converter o índice, subtraindo 1 ao valor usado no programa original.

Também existiram limitações nas instruções de entrada e saída, como o PRINT, READ e WRITE. O PRINT e o READ foram implementados de forma funcional mas ainda com limitações, especialmente no suporte a formatos mais complexos. Já o WRITE não foi implementado, uma vez que a sua sintaxe causava conflitos shift/reduce no parser. Para resolver este conflito, seria preciso realizar alterações significativas na gramática e em várias partes do projeto. Po isso, optou-se por limitar o compilador nesse sentido e focar na implementação de outras funcionalidades e otimizações igualmente importantes.

Assim, apesar do compilador já conseguir traduzir vários programas simples em Fortran77 para código máquina EWVM, ainda existem algumas limitações. No entanto, consideramos que foram superadas várias dificuldades ao longo da realização do projeto, o que nos permitiu compreender melhor o funcionamento de um compilador e a sintaxe de uma linguagem que não conhecíamos.

---

## 9. Otimizações Implementadas

Para além de garantir a correta tradução e integridade semântica do código Fortran 77, o compilador inclui otimizações diretamente no `Translator`. O objetivo principal destas transformações é melhorar a eficiência do código gerado para a Máquina Virtual, reduzindo o número de instruções a executar, poupando espaço na memória e eliminando redundâncias computacionais.


### 9.1. Constant Folding
A constant folding é uma técnica que avalia operações aritméticas ou lógicas entre valores constantes diretamente em tempo de compilação, em vez de gerar código para que a máquina virtual faça esses cálculos em tempo de execução. Durante a tradução do código, são encontradas expressões cujos operandos são literais conhecidos (como números inteiros ou reais), ele calcula o resultado imediatamente e substitui todo o nó da operação por um único nó. Por exemplo:

Para o código 
```
      X = 3 + 5 * 2
``` 

Seriam gerados os seguintes comandos:

`PUSHI 3` -> `PUSHI 5` -> `PUSHI 2` -> `MUL` -> `ADD` -> `STOREG 0`

Com a otimização, o `Translator` faz os cálculos e seria apenas gerado:

`PUSHI 13` -> `STOREG 0`

### 9.2. Eliminação de Código Morto
A otimização de código morto é implementada no `Translator` em estruturas condicionais IF e foca-se em limpar o programa de quaisquer blocos de instruções que nunca serão alcançados pela execução. 

Se o tradutor determinar que a condição de um IF é estritamente falsa, todo o bloco de instruções principal (THEN) é sumariamente ignorado e descartado do ficheiro final, gerando apenas código relativo ao ELSE. Por exemplo:

Para o código
```
      IF (.FALSE.) THEN
          X = 10
      ELSE
          X = 20
      ENDIF
```
é apenas gerado 
`PUSHI 20` -> `STOREG 0`

### 9.3. Remoção de Ciclos Mortos
A remoção de ciclos mortos deteta loops DO que nunca chegam a realizar uma única iteração. Ao analisar as instruções de um ciclo, o tradutor compara o limite inicial com o limite final fornecido e tem em consideração a direção do step.

Se for detetado um ciclo onde o valor inicial já ultrapassou o objetivo logo à partida (como no exemplo abaixo), o `Translator` reconhece que é código que nunca será executado e, em vez de gastar memória a criar variáveis de iteração na stack e a gerar etiquetas de ciclo, ignora completamente o nó e passa à instrução seguinte.

Para o código
```
      DO 10 I = 10, 1, 1
          X = X + I
10    CONTINUE
```
não é gerado nenhum comando para este ciclo, já que 10 é maior que 1 e é um ciclo com um incremento positivo.


### 9.4. Eliminação de Dupla Negação

A eliminação de dupla negação atua especificamente sobre expressões lógicas e booleanas que possuam inversões consecutivas. 

Ao intersetar este padrão lógico durante a tradução, o `Translator` anula ambas as operações. Na máquina virtual, isto traduz-se diretamente na remoção de instruções repetidas `NOT`, otimizando o fluxo lógico que decide os desvios no programa. Por exemplo:

Para o código
```
      IF (.NOT. (.NOT. FLAG)) THEN
```
Sem otimizações, seria gerado:
`PUSHG 0` -> `NOT` -> `NOT` -> `JZ label_else`

Com a otimização:
`PUSHG 0` -> `JZ label_else`


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
