C     TESTE 3: Eliminacao de Loop Morto (Dead Loop Elimination)
C     Um DO com start > end nunca executa.
C     O compilador deve detectar isso em compile-time e nao gerar codigo para o corpo.
      PROGRAM TESTDL
      INTEGER I, SOMA

      SOMA = 0

C     Loop normal: executa 5 vezes
      DO 10 I = 1, 5
        SOMA = SOMA + I
   10 CONTINUE
      PRINT *, 'SOMA apos loop normal (esperado 15): ', SOMA

C     Loop morto: start (10) > end (1), nunca deve executar
      DO 20 I = 10, 1
        SOMA = SOMA + 999
   20 CONTINUE
      PRINT *, 'SOMA apos loop morto (esperado 15): ', SOMA

C     Loop morto: start == end + 1
      DO 30 I = 5, 4
        SOMA = SOMA + 999
   30 CONTINUE
      PRINT *, 'SOMA final (esperado 15): ', SOMA

      END
