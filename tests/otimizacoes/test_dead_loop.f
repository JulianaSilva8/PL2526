      PROGRAM TESTDL
      INTEGER I, SOMA

      SOMA = 0

      DO 10 I = 1, 5
        SOMA = SOMA + I
   10 CONTINUE
      PRINT *, 'SOMA apos ciclo normal (esperado 15): ', SOMA

      DO 20 I = 10, 1
        SOMA = SOMA + 999
   20 PRINT *, 'EXECUTEI ISTO'
      PRINT *, 'SOMA apos ciclo morto (esperado 15): ', SOMA

      DO 30 I = 5, 4
        SOMA = SOMA + 999
   30 CONTINUE
      PRINT *, 'SOMA final (esperado 15): ', SOMA

      STOP
      END
