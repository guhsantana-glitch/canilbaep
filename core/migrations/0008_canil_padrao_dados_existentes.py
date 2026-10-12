from django.db import migrations


def criar_canil_padrao(apps, schema_editor):
    Canil = apps.get_model("canis", "Canil")
    Unidade = apps.get_model("canis", "Unidade")
    unidade, _ = Unidade.objects.get_or_create(
        nome="10º BAEP", defaults={"cidade_sede": "Piracicaba", "ativo": True}
    )
    canil, _ = Canil.objects.get_or_create(
        nome="10º BAEP – Canil Sumaré",
        defaults={"unidade": unidade, "cidade": "Sumaré", "ativo": True},
    )
    for modelo in ("Cao", "Condutor", "Veterinario", "TipoVacina"):
        apps.get_model("core", modelo).objects.filter(canil__isnull=True).update(canil=canil)


def reverso(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("canis", "0004_canil_unidade_obrigatoria"),
        ("core", "0007_cao_canil_condutor_canil_tipovacina_canil_and_more"),
    ]

    operations = [
        migrations.RunPython(criar_canil_padrao, reverso),
    ]
