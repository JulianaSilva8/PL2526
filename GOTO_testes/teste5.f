C     Deve dar erro (Cross-scope)      --nao passou
      PROGRAM TEST
      INTEGER I
      GOTO 100
      END

      INTEGER FUNCTION FOO()
      FOO = 1
100   CONTINUE
      RETURN
      END