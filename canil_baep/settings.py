"""
Django settings for canil_baep project (Sistema de Gestão do Canil - 10° BAEP).
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")  # carrega variáveis do .env em desenvolvimento local

# SECURITY: em produção, defina a variável de ambiente DJANGO_SECRET_KEY
CHAVE_PADRAO = "django-insecure-CHANGE-ME-antes-de-colocar-em-producao"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or CHAVE_PADRAO

# Fail-closed: DEBUG desligado por padrão (nunca expor traceback em produção).
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"

if not DEBUG and SECRET_KEY == CHAVE_PADRAO:
    raise ImproperlyConfigured(
        "Defina DJANGO_SECRET_KEY (string aleatória longa) no ambiente antes de rodar. "
        "Gere uma com: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
    )

RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
CSRF_TRUSTED_ORIGINS = [
    o for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o
]
if RENDER_EXTERNAL_HOSTNAME and f"https://{RENDER_EXTERNAL_HOSTNAME}" not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'canis',
    'gestaocanis',
    'racoes',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'canis.middleware.CanilMiddleware',
    'canis.middleware.SenhaTemporariaMiddleware',
]

ROOT_URLCONF = 'canil_baep.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'canil_baep.wsgi.application'

# Banco de dados: SQLite local. Em produção, DATABASE_URL do Neon
# (Postgres gratuito que não expira). Neon usa pooler (pgbouncer):
# sem conexões persistentes, senão o servidor fecha a conexão
# ociosa -> "SSL connection has been closed unexpectedly".
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=0,
        conn_health_checks=True,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# === Arquivos na nuvem (storage S3: Cloudflare R2 ou Supabase, gratuitos) ===
# Sem essas variáveis, usa a pasta local (desenvolvimento).
# Com elas, fotos/documentos vão para o bucket e sobrevivem aos
# deploys do Render (cujo disco é efêmero e apaga tudo a cada deploy).
# Veja o README (seção Deploy) para criar o bucket e as chaves.
#
# PRIVACIDADE: os arquivos NUNCA ficam públicos. O acesso usa URL assinada
# (com validade curta) gerada pelo próprio S3 — só quem tem o link recebe.
# Só ative MEDIA_PUBLICA=1 se quiser bucket público de verdade (recomendável: NÃO).
STORAGE_BUCKET = os.environ.get("STORAGE_BUCKET", "") or os.environ.get("R2_BUCKET", "")
MEDIA_PUBLICA = os.environ.get("MEDIA_PUBLICA", "0") in ("1", "true", "True")
if STORAGE_BUCKET:
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "access_key": os.environ.get("STORAGE_ACCESS_KEY", "") or os.environ.get("R2_ACCESS_KEY", ""),
                "secret_key": os.environ.get("STORAGE_SECRET_KEY", "") or os.environ.get("R2_SECRET_KEY", ""),
                "bucket_name": STORAGE_BUCKET,
                "endpoint_url": os.environ.get("STORAGE_ENDPOINT_URL", "") or os.environ.get("R2_ENDPOINT_URL", ""),
                "region_name": os.environ.get("STORAGE_REGION", "auto"),
                "addressing_style": os.environ.get("STORAGE_ADDRESSING_STYLE") or None,
                "default_acl": None,
                # URL assinada com validade curta: impede download anônimo/vazamento.
                "querystring_auth": not MEDIA_PUBLICA,
                "querystring_expire": int(os.environ.get("STORAGE_URL_EXPIRES", "600")),
                "custom_domain": (
                    (os.environ.get("STORAGE_PUBLIC_URL", "") or os.environ.get("R2_PUBLIC_URL", ""))
                    if MEDIA_PUBLICA else ""
                ),
                "location": "media",
            },
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    # Observação: com S3 privado, `arquivo.url` já devolve a URL assinada do
    # próprio bucket (o django-storages ignora MEDIA_URL nesse caso).
    # MEDIA_URL continua "/media/" para o armazenamento local em disco.

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'lista_caes'
LOGOUT_REDIRECT_URL = 'login'

# === Cabeçalhos de segurança HTTP (fail-safe: só desligado em DEBUG) ===
def _flag(nome, padrao="True"):
    return os.environ.get(nome, padrao) in ("1", "true", "True")


# Render fica atrás de proxy TLS: confia no X-Forwarded-Proto para o redirect.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = not DEBUG and _flag("DJANGO_SSL_REDIRECT")
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "0" if DEBUG else "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = False  # só ative se o domínio for 100% HTTPS
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = False  # o JS deaboque de CSRF depende do cookie
CSRF_COOKIE_SAMESITE = "Lax"
# Limites de upload (fotos/documentos)
DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
# Bloqueia brute-force no login (cache local por usuário+IP)
LOGIN_MAX_TENTATIVAS = int(os.environ.get("LOGIN_MAX_TENTATIVAS", "8"))
LOGIN_BLOQUEIO_MINUTOS = int(os.environ.get("LOGIN_BLOQUEIO_MINUTOS", "15"))
