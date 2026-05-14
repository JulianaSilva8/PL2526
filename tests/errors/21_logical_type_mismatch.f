      PROGRAM LOGIC_TYPE_MISMATCH
      INTEGER A
      LOGICAL B
      A = 1
      B = .TRUE.
      B = A .AND. B
      END
