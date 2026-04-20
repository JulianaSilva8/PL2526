      PROGRAM CALC
      REAL X, Y, DIF, QUOC
      LOGICAL VALIDO

      PRINT *, 'INTRODUZA DOIS VALORES:'
      READ *, X, Y

      DIF = X - Y
      VALIDO = .FALSE.

      IF (Y .NE. 0.0) THEN
          QUOC = X / Y
          VALIDO = .TRUE.
      ENDIF

      PRINT *, 'DIFERENCA = ', DIF
      PRINT *, 'DIVISAO VALIDA? ', VALIDO

      END