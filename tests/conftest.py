import os

# O app lê Settings no import; valores só para o teste (nada é chamado de verdade).
for chave, valor in {
    "API_URL": "http://core.invalid",
    "API_KEY": "k",
    "API_SECRET": "s",
    "AUTH_URL": "http://entra.invalid",
    "AUTH_TENANT": "t",
    "AUTH_CLIENT_ID": "c",
    "AUTH_CLIENT_SECRET": "s",
    "SESSION_SECRET": "segredo-de-teste-com-32-bytes-ou-mais-ok",
}.items():
    os.environ.setdefault(chave, valor)
