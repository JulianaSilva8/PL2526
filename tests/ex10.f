      PROGRAM TESTALL
      INTEGER A(3)
      INTEGER I
      CHARACTER*5 NOME
      CHARACTER*10 CIDADE

      A(1) = 10
      A(2) = 20
      A(3) = 30

      NOME = 'ANA'
      CIDADE = 'PORTO'

      PRINT *, NOME
      PRINT *, CIDADE

      DO 100 I = 1, 3
 100  PRINT *, A(I)

      STOP
      END