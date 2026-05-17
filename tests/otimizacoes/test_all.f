C     TESTE: Combinacao de Otimizacoes
C     Valida que as quatro otimizacoes funcionam em conjunto no mesmo programa.
C     Resultados esperados:
C       X = 111  (constant folding decide o ramo do IF)
C       Y = 100  (dead code: IF .FALSE. nao altera Y)
C       SOMA = 0 (ciclo morto nao executa)
      PROGRAM TESTCOMBO
      INTEGER X, Y, I, SOMA
      LOGICAL FLAG

      X = 0
      Y = 100
      SOMA = 0
      FLAG = .TRUE.

C     Constant folding + dead code:
C     13 .GT. 17 e calculado em compile-time -> .FALSE. -> so o ELSE executa
      IF (10 + 3 .GT. 12 + 5) THEN
        X = 999
      ELSE
        X = 111
      ENDIF
      PRINT *, 'X (esperado 111): ', X

C     Dead code: condicao .FALSE. literal -> Y nao muda
      IF (.NOT. (.NOT. (.FALSE.))) THEN
        Y = 555
      ENDIF
      PRINT *, 'Y (esperado 100): ', Y

C     Ciclo morto: start (20) > end (10) com step positivo -> nao executa
      DO 10 I = 20, 10, 1
        SOMA = SOMA + I
   10 CONTINUE
      PRINT *, 'SOMA (esperado 0): ', SOMA

      STOP
      END
