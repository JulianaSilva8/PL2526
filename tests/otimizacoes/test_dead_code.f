C     TESTE: Eliminacao de Codigo Morto
C     Quando a condicao de um IF e um literal, o ramo morto nao deve
C     gerar codigo. Para verificar: o codigo EWVM nao deve conter
C     instrucoes para os blocos que nunca executam (ex: PUSHI 999).
      PROGRAM TESTDCE
      INTEGER X

C     Condicao .TRUE. literal: so o THEN deve gerar codigo
C     O ELSE (X = 0) nao deve aparecer no ficheiro EWVM
      IF (.TRUE.) THEN
        X = 42
      ELSE
        X = 0
      ENDIF
      PRINT *, 'X (esperado 42): ', X

C     Condicao .FALSE. literal: so o ELSE deve gerar codigo
C     O THEN (X = 999) nao deve aparecer no ficheiro EWVM
      IF (.FALSE.) THEN
        X = 999
      ELSE
        X = 7
      ENDIF
      PRINT *, 'X (esperado 7): ', X

C     Condicao .FALSE. sem ELSE: o bloco inteiro deve ser ignorado
      X = 55
      IF (.FALSE.) THEN
        X = 1
      ENDIF
      PRINT *, 'X (esperado 55): ', X

      STOP
      END
