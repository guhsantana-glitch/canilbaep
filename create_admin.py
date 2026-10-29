"""Cria o superusuário inicial a partir de variáveis de ambiente.

Uso (local):
    set ADMIN_USERNAME=seu-usuario
    set ADMIN_PASSWORD=uma-senha-forte
    .\venv\Scripts\python.exe create_admin.py

Em produção (Render), use o shell ou um script equivalente — nunca
deixe senhas fixas neste arquivo.
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "canil_baep.settings")

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402

User = get_user_model()

username = os.environ.get("ADMIN_USERNAME", "").strip()
password = os.environ.get("ADMIN_PASSWORD", "")
email = os.environ.get("ADMIN_EMAIL", "").strip()

if not username or not password:
    raise SystemExit(
        "Defina ADMIN_USERNAME e ADMIN_PASSWORD no ambiente antes de rodar."
    )

if User.objects.filter(username=username).exists():
    print("Usuário já existe!")
else:
    User.objects.create_superuser(username=username, password=password, email=email)
    print(f"Superusuário '{username}' criado!")