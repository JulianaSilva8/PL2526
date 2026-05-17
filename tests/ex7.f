      program calc
      real X, Y, DIF, QUOC
      LOGICAL VALIDO

      PRINT *, 'INTRODUZA DOIS VALORES:'
      read *, X, Y

      DIF = X - Y
      VALIDO = .false.

      IF (Y .NE. 0.0) THEN
          QUOC = X / Y
          VALIDO = .TRUE.
      endif

      PRINT *, 'DIFERENCA = ', DIF
      print *, 'DIVISAO VALIDA? ', VALIDO

      end