from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum


class Racao(models.Model):
    """Tipo de ração do canil (cadastro)."""

    canil = models.ForeignKey(
        "canis.Canil", on_delete=models.CASCADE, related_name="racoes",
        verbose_name="Canil",
    )
    nome = models.CharField("Nome da ração", max_length=100)
    marca = models.CharField("Marca/Fabricante", max_length=100, blank=True)
    descricao = models.CharField("Descrição", max_length=200, blank=True)
    estoque_minimo_kg = models.DecimalField(
        "Estoque mínimo (kg)", max_digits=8, decimal_places=2, default=0,
        help_text="Abaixo disso o item aparece em alerta.",
    )
    ativo = models.BooleanField("Ativo", default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ração"
        verbose_name_plural = "Rações"
        ordering = ["nome"]
        constraints = [
            models.UniqueConstraint(fields=["canil", "nome"], name="uniq_racao_canil_nome")
        ]

    def __str__(self):
        return self.nome

    def estoque_kg(self):
        entradas = self.movimentacoes.filter(tipo=MovimentacaoRacao.Tipo.ENTRADA).aggregate(
            total=Sum("quantidade_kg"))["total"] or 0
        saidas = self.movimentacoes.filter(tipo=MovimentacaoRacao.Tipo.SAIDA).aggregate(
            total=Sum("quantidade_kg"))["total"] or 0
        return entradas - saidas

    def em_alerta(self):
        return self.estoque_kg() <= self.estoque_minimo_kg


class MovimentacaoRacao(models.Model):
    """Entrada ou saída de ração do estoque (auditoria completa)."""

    class Tipo(models.TextChoices):
        ENTRADA = "ENTRADA", "Entrada"
        SAIDA = "SAIDA", "Saída"

    racao = models.ForeignKey(Racao, on_delete=models.PROTECT, related_name="movimentacoes")
    tipo = models.CharField("Tipo", max_length=10, choices=Tipo.choices)
    data = models.DateField("Data")
    quantidade_kg = models.DecimalField("Quantidade (kg)", max_digits=8, decimal_places=2)
    responsavel = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="movimentacoes_racao",
        verbose_name="Responsável",
        help_text="Usuário logado que lançou a transação (preenchido automaticamente).",
    )
    motivo = models.CharField("Motivo/Observação", max_length=200, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Movimentação de ração"
        verbose_name_plural = "Movimentações de ração"
        ordering = ["-data", "-criado_em"]

    def __str__(self):
        return f"{self.get_tipo_display()} {self.quantidade_kg}kg - {self.racao.nome} ({self.data})"
