from django.db import migrations


def migrar_unidades(apps, schema_editor):
    Canil = apps.get_model("canis", "Canil")
    Unidade = apps.get_model("canis", "Unidade")
    for canil in Canil.objects.all():
        nome = (canil.unidade_nome_antigo or "").strip() or "Unidade a definir"
        unidade, _ = Unidade.objects.get_or_create(nome=nome)
        canil.unidade = unidade
        canil.save(update_fields=["unidade"])


def reverso(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("canis", "0002_unidade_canil_unidade_nome_antigo_and_more"),
    ]

    operations = [
        migrations.RunPython(migrar_unidades, reverso),
    ]
