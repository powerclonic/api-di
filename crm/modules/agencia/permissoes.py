"""Roles do Entra (claim `roles`) do domínio "agência". Um usuário pode ter um, outro ou os dois.
Cada domínio declara os seus (ex.: um módulo de crédito teria os dele); `shared/auth.py` só tem
o mecanismo (`requer_role`)."""

OPERADOR = "app_crm_agencia_operador"
ADMINISTRADOR = "app_crm_agencia_administrador"

# Quem opera no dia a dia da agência: operador OU administrador.
OPERACAO = (OPERADOR, ADMINISTRADOR)
