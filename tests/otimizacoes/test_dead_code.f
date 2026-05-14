C     TESTE 2: Dead Code Elimination
C     Quando a condicao de um IF e um literal, o ramo morto nao deve
C     gerar codigo (nem JZ/JUMP desnecessarios).
      PROGRAM TESTDCE
      INTEGER X

C     Ramo THEN sempre executado (condicao .TRUE.)
      IF (.TRUE.) THEN
        X = 42
      ELSE
        X = 0
      ENDIF
      PRINT *, 'X (esperado 42): ', X

C     Ramo ELSE nunca executado (condicao .FALSE.)
      IF (.FALSE.) THEN
        X = 999
      ELSE
        X = 7
      ENDIF
      PRINT *, 'X (esperado 7): ', X

C     Sem ELSE, condicao falsa -> nada deve acontecer
      X = 55
      IF (.FALSE.) THEN
        X = 1
      ENDIF
      PRINT *, 'X (esperado 55): ', X

      END
