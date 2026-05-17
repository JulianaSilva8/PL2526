#!/bin/bash

# deteção de erros
TEST_DIR="tests/errors"
TEST_DIR_SUCCESS="tests"
TEST_OTIMIZATION_SUCCESS="tests/otimizacoes"
MAIN_FILE="main.py"

FAIL_COUNT=0
TOTAL_TESTS=0

for file in "$TEST_DIR"/*; do
    if [ -f "$file" ]; then
        ((TOTAL_TESTS++))
        echo -n "Teste: $(basename "$file")... "
        
        output=$(python3 "$MAIN_FILE" "$file" 2>&1)

        # verifica se a string de sucesso aparece no output
        if echo "$output" | grep -q "Successfully translated to output.txt"; then
            echo "FALHOU! (erro não detetado)"
            ((FAIL_COUNT++))
        else
            echo "OK"
        fi
    fi
done

for file in "$TEST_DIR_SUCCESS"/*; do
    if [ -f "$file" ]; then
        ((TOTAL_TESTS++))
        echo -n "Teste: $(basename "$file")... "
        
        output=$(python3 "$MAIN_FILE" "$file" 2>&1)

        # verifica se a string de sucesso aparece no output
        if echo "$output" | grep -q "Successfully translated to output.txt"; then
            echo "OK"
        else
            echo "FALHOU! (erro detetado)"
            ((FAIL_COUNT++))
        fi
    fi
done

for file in "$TEST_OTIMIZATION_SUCCESS"/*; do
    if [ -f "$file" ]; then
        ((TOTAL_TESTS++))
        echo -n "Teste: $(basename "$file")... "

        output=$(python3 "$MAIN_FILE" "$file" 2>&1)

        # verifica se a string de sucesso aparece no output
        if echo "$output" | grep -q "Successfully translated to output.txt"; then
            echo "OK"
        else
            echo "FALHOU! (erro detetado)"
            ((FAIL_COUNT++))
        fi
    fi
done

echo "-------------------------------------------"
echo "Testes falhados: $FAIL_COUNT"

# Sai com código de erro se algum teste falhou
if [ $FAIL_COUNT -ne 0 ]; then
    exit 1
fi