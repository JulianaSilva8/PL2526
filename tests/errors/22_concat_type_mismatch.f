      PROGRAM CONCAT_TYPE_MISMATCH
      CHARACTER*5 STR
      REAL X
      STR = 'HELLO'
      X = 3.14
      STR = STR // X
      END
