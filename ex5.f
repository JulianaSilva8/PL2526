      PROGRAM CONVERSOR
      INTEGER NUM, BASE, RESULT, CONVRT
C
      PRINT *, 'INTRODUZA UM NUMERO DECIMAL INTEIRO:'
      READ *, NUM
C
      DO 10 BASE = 2, 9
          RESULT = CONVRT(NUM, BASE)
          PRINT *, 'BASE ', BASE, ': ', RESULT
   10 CONTINUE
C
      END
C
      INTEGER FUNCTION CONVRT(N, B)
      INTEGER N, B, QUOT, REM, POT, VAL
      VAL = 0
      POT = 1
      QUOT = N
   20 IF (QUOT .GT. 0) THEN
          REM = MOD(QUOT, B)
          VAL = VAL + (REM * POT)
          QUOT = QUOT / B
          POT = POT * 10
          GOTO 20
      ENDIF
      CONVRT = VAL
      RETURN
      END