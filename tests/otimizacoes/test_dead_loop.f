C     TESTE: Eliminacao de Ciclos Mortos
C     Um DO cujo limite inicial ja ultrapassa o limite final nunca executa.
C     Para verificar: o codigo EWVM nao deve conter instrucoes relativas
C     ao corpo dos ciclos mortos (ex: nao deve aparecer PUSHI 999).
      PROGRAM TESTDL
      INTEGER I, SOMA

      SOMA = 0

C     Ciclo normal: start (1) <= end (5), executa 5 vezes -> SOMA = 15
      DO 10 I = 1, 5
        SOMA = SOMA + I
   10 CONTINUE
      PRINT *, 'SOMA apos ciclo normal (esperado 15): ', SOMA

C     Ciclo morto: start (10) > end (1), step positivo por omissao
C     Nunca deve executar -> SOMA permanece 15
      DO 20 I = 10, 1
        SOMA = SOMA + 999
   20 PRINT *, 'EXECUTEI ISTO'
      PRINT *, 'SOMA apos ciclo morto (esperado 15): ', SOMA

C     Ciclo morto: start (5) > end (4), step positivo
C     Nunca deve executar -> SOMA permanece 15
      DO 30 I = 5, 4
        SOMA = SOMA + 999
   30 CONTINUE
      PRINT *, 'SOMA final (esperado 15): ', SOMA

      STOP
      END
