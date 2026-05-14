C     TESTE 4: Eliminacao de Dupla Negacao (.NOT. .NOT.)
C     .NOT. .NOT. X e logicamente equivalente a X.
C     O compilador deve simplificar isto sem gerar instrucoes extra.
      PROGRAM TESTNN
      LOGICAL A, B, C

      A = .TRUE.
      B = .NOT. A
      C = .NOT. B

      PRINT *, 'A (esperado 1): ', A
      PRINT *, 'B (esperado 0): ', B
      PRINT *, 'C (esperado 1): ', C

C     Dupla negacao em expressao relacional
      INTEGER X
      LOGICAL R
      X = 5
      R = .NOT. .NOT. (X .GT. 3)
      PRINT *, 'R (esperado 1): ', R

C     Tripla negacao: NOT NOT NOT X = NOT X
      LOGICAL D
      D = .NOT. .NOT. .NOT. A
      PRINT *, 'D (esperado 0): ', D

      END
