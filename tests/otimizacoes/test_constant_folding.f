      PROGRAM TESTCF
      INTEGER A, B, C
      A = 3 + 4
      B = 10 - 2
      C = A + B
      PRINT *, 'A (esperado 7): ', A
      PRINT *, 'B (esperado 8): ', B
      PRINT *, 'C (esperado 15): ', C

C     Tambem para reais
      REAL X, Y
      X = 2.5 + 1.5
      Y = 10.0 / 4.0
      PRINT *, 'X (esperado 4): ', X
      PRINT *, 'Y (esperado 2.5): ', Y

C     Expressoes relacionais entre literais
      LOGICAL FLAG
      FLAG = 3 .LT. 10
      PRINT *, 'FLAG (esperado 1): ', FLAG

      END
