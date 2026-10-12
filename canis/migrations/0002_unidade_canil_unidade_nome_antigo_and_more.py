# Ajustada manualmente: preserva os dados da coluna `unidade` (texto)
# renomeando-a para `unidade_nome_antigo` em vez de alterar o tipo.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('canis', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Unidade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=150, unique=True, verbose_name='Nome da unidade (ex: 10º BAEP)')),
                ('cidade_sede', models.CharField(blank=True, max_length=100, verbose_name='Cidade sede')),
                ('comandante', models.CharField(blank=True, max_length=150, verbose_name='Comandante responsável')),
                ('telefone', models.CharField(blank=True, max_length=20, verbose_name='Telefone')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='E-mail')),
                ('ativo', models.BooleanField(default=True, help_text='Unidade desativada bloqueia a criação de novos canis nela.', verbose_name='Ativa')),
                ('observacoes', models.TextField(blank=True, verbose_name='Observações')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Unidade',
                'verbose_name_plural': 'Unidades',
                'ordering': ['nome'],
            },
        ),
        migrations.RenameField(
            model_name='canil',
            old_name='unidade',
            new_name='unidade_nome_antigo',
        ),
        migrations.AddField(
            model_name='canil',
            name='unidade',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='canis', to='canis.unidade', verbose_name='Unidade'),
        ),
    ]
