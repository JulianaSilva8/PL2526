      PROGRAM TESTDCE
      INTEGER X

      IF (.TRUE.) THEN
        X = 42
      ELSE
        X = 0
      ENDIF
      PRINT *, 'X (esperado 42): ', X

      IF (.FALSE.) THEN
        X = 999
      ELSE
        X = 7
      ENDIF
      PRINT *, 'X (esperado 7): ', X

      X = 55
      IF (.FALSE.) THEN
        X = 1
      ENDIF
      PRINT *, 'X (esperado 55): ', X

      STOP
      END
