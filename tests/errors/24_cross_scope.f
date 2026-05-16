C     Tem que dar erro(cross-scope)
      PROGRAM TEST
      INTEGER I
100   CONTINUE
      END

      INTEGER FUNCTION FOO()
      FOO = 1
      GOTO 100
      RETURN
      END