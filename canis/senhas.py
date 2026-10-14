"""Geração de senhas iniciais de usuários do sistema."""

from django.utils.crypto import get_random_string

# Senha padrão preenchida na criação de usuários (o usuário é obrigado
# a trocá-la no primeiro acesso).
SENHA_PADRAO = "canil123"

CARACTERES_SENHA = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"

# Prazo para trocar a senha temporária. Vencido o prazo sem troca,
# o acesso é bloqueado e o usuário deve falar com o desenvolvedor.
PRAZO_TROCA_SENHA_DIAS = 7


def gerar_senha_aleatoria(tamanho=10):
    """Gera uma senha aleatória legível (sem caracteres ambíguos)."""
    return get_random_string(tamanho, allowed_chars=CARACTERES_SENHA)


def inicio_prazo_senha(vinculo):
    """Data/hora de início do prazo (emissão ou, p/ vínculos antigos, criação)."""
    if vinculo is None:
        return None
    return getattr(vinculo, "senha_temporaria_em", None) or getattr(vinculo, "criado_em", None)


def limite_troca_senha(vinculo):
    """Data/hora limite para a troca, ou None se não há prazo pendente."""
    from datetime import timedelta

    if vinculo is None or not vinculo.senha_temporaria:
        return None
    inicio = inicio_prazo_senha(vinculo)
    if inicio is None:
        return None
    return inicio + timedelta(days=PRAZO_TROCA_SENHA_DIAS)


def senha_temporaria_expirada(vinculo, agora=None):
    """True se passou o prazo de 7 dias sem a troca."""
    from django.utils import timezone

    if vinculo is None or not vinculo.senha_temporaria:
        return False
    limite = limite_troca_senha(vinculo)
    if limite is None:
        return False
    return (agora or timezone.now()) > limite


def dias_restantes_senha(vinculo, agora=None):
    """Dias restantes (arredondado p/ cima); 0 se expirado ou sem prazo."""
    import math

    from django.utils import timezone

    if vinculo is None or not vinculo.senha_temporaria:
        return 0
    limite = limite_troca_senha(vinculo)
    if limite is None:
        return 0
    segundos = (limite - (agora or timezone.now())).total_seconds()
    if segundos <= 0:
        return 0
    return int(math.ceil(segundos / 86400))
