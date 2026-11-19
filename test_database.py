
from database import (
    criar_conta,
    listar_contas,
    listar_categorias,
    obter_resumo
)

# Criar uma conta inicial, caso ainda não exista
if not listar_contas():
    criar_conta(
        nome="Conta principal",
        tipo="checking",
        saldo_inicial=0
    )

print("\n===== FINANCE MANAGER =====")

print("\nCONTAS:")
for conta in listar_contas():
    print(conta)

print("\nCATEGORIAS:")
for categoria in listar_categorias():
    print(categoria)

print("\nRESUMO FINANCEIRO:")
print(obter_resumo())
