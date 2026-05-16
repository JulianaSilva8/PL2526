      PROGRAM TEST_COMBO
      INTEGER X, Y, I
      LOGICAL FLAG
      
      X = 0
      Y = 100
      FLAG = .TRUE.


      IF (10 + 3 .GT. 12 + 5) THEN
          X = 999
      ELSE
          X = 111
      ENDIF


      IF (.NOT. (.NOT. (.FALSE.))) THEN
          Y = 555
      ENDIF


      DO 10 I = 20, 10, 1
          X = X + I
10    CONTINUE

      PRINT *, X
      PRINT *, Y
      END