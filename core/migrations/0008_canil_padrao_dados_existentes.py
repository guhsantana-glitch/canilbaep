from django.db import migrations


def criar_canil_padrao(apps, schema_editor):
    Canil = apps.get_model("canis", "Canil")
    canil, _ = Canil.objects.get_or_create(
        nome="10º BAEP – Canil Sumaré",
        defaults={"unidade": "10º BAEP", "cidade": "Sumaré", "ativo": True},
    )
    for modelo in ("Cao", "Condutor", "Veterinario", "TipoVacina"):
        apps.get_model("core", modelo).objects.filter(canil__isnull=True).update(canil=canil)


def reverso(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("canis", "0001_initial"),
        ("core", "0007_cao_canil_condutor_canil_tipovacina_canil_and_more"),
    ]

    operations = [
        migrations.RunPython(criar_canil_padrao, reverso),
    ]
