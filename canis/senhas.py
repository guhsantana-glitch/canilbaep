"""Geração de senhas iniciais de usuários do sistema."""

from django.utils.crypto import get_random_string

# Senha padrão preenchida na criação de usuários (o usuário é obrigado
# a trocá-la no primeiro acesso).
SENHA_PADRAO = "canil123"

CARACTERES_SENHA = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"


def gerar_senha_aleatoria(tamanho=10):
    """Gera uma senha aleatória legível (sem caracteres ambíguos)."""
    return get_random_string(tamanho, allowed_chars=CARACTERES_SENHA)
