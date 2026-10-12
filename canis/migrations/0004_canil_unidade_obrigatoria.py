import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("canis", "0003_migrar_unidades_existentes"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="canil",
            name="unidade_nome_antigo",
        ),
        migrations.AlterField(
            model_name="canil",
            name="unidade",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="canis", to="canis.unidade", verbose_name="Unidade"),
        ),
    ]
