      PROGRAM TESTCOMBO
      INTEGER X, Y, I, SOMA
      LOGICAL FLAG

      X = 0
      Y = 100
      SOMA = 0
      FLAG = .TRUE.
      IF (10 + 3 .GT. 12 + 5) THEN
        X = 999
      ELSE
        X = 111
      ENDIF
      PRINT *, 'X (esperado 111): ', X

      IF (.NOT. (.NOT. (.FALSE.))) THEN
        Y = 555
      ENDIF
      PRINT *, 'Y (esperado 100): ', Y

      DO 10 I = 20, 10, 1
        SOMA = SOMA + I
   10 CONTINUE
      PRINT *, 'SOMA (esperado 0): ', SOMA

      STOP
      END
