      PROGRAM COMP
      INTEGER A, B, MAIOR
      LOGICAL IGUAIS

      PRINT *, 'INTRODUZA DOIS NUMEROS:'
      READ *, A, B

      IGUAIS = .FALSE.

      IF (A .EQ. B) THEN
          IGUAIS = .TRUE.
          MAIOR = A
      ELSE
          IF (A .GT. B) THEN
              MAIOR = A
          ELSE
              MAIOR = B
          ENDIF
      ENDIF

      PRINT *, 'MAIOR = ', MAIOR
      PRINT *, 'IGUAIS? ', IGUAIS

      END