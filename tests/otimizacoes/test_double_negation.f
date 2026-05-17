C     TESTE: Eliminacao de Dupla Negacao
C     .NOT. .NOT. X e logicamente equivalente a X.
C     Para verificar: no codigo EWVM nao devem aparecer duas instrucoes
C     NOT consecutivas para os casos de dupla negacao.
      PROGRAM TESTNN
      LOGICAL A, B, C, D, R
      INTEGER X

      A = .TRUE.
      B = .NOT. A
      C = .NOT. B

      PRINT *, 'A (esperado 1): ', A
      PRINT *, 'B (esperado 0): ', B
      PRINT *, 'C (esperado 1): ', C

C     Dupla negacao direta em expressao relacional:
C     .NOT. .NOT. (X .GT. 3) deve gerar o mesmo codigo que (X .GT. 3)
      X = 5
      R = .NOT. .NOT. (X .GT. 3)
      PRINT *, 'R (esperado 1): ', R

C     Tripla negacao: .NOT. .NOT. .NOT. A equivale a .NOT. A
C     Deve gerar apenas um NOT no codigo EWVM
      D = .NOT. .NOT. .NOT. A
      PRINT *, 'D (esperado 0): ', D

      STOP
      END
