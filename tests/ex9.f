      PROGRAM TESTCALL
      INTEGER A
      INTEGER B

      A = 10
      B = 20

      CALL SHOW(A, B)

      STOP
      END

      SUBROUTINE SHOW(X, Y)
      INTEGER X
      INTEGER Y

      PRINT *, 'X = ', X
      PRINT *, 'Y = ', Y

      RETURN
      END