import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "canil_baep.settings")

django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = "Gava"
password = "canil2026"

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(
        username=username,
        password=password,
        email="gava@email.com"
    )
    print("Usuário criado!")
else:
    print("Usuário já existe!")