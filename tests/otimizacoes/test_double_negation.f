      PROGRAM TESTNN
      LOGICAL A, B, C, D, R
      INTEGER X

      A = .TRUE.
      B = .NOT. A
      C = .NOT. B

      PRINT *, 'A (esperado 1): ', A
      PRINT *, 'B (esperado 0): ', B
      PRINT *, 'C (esperado 1): ', C

      X = 5
      R = .NOT. .NOT. (X .GT. 3)
      PRINT *, 'R (esperado 1): ', R

      D = .NOT. .NOT. .NOT. A
      PRINT *, 'D (esperado 0): ', D

      STOP
      END
