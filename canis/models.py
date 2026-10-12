from django.db import models
from django.contrib.auth.models import User


class Canil(models.Model):
    """Cada canil setorial da PM que utiliza o sistema (tenant)."""

    nome = models.CharField("Nome do canil", max_length=150)
    unidade = models.CharField("Batalhão/Unidade (ex: 10º BAEP)", max_length=100, blank=True)
    cidade = models.CharField("Cidade", max_length=100, blank=True)
    responsavel = models.CharField("Responsável", max_length=150, blank=True)
    telefone = models.CharField("Telefone", max_length=20, blank=True)
    email = models.EmailField("E-mail", blank=True)
    ativo = models.BooleanField(
        "Ativo", default=True,
        help_text="Canil desativado tem o acesso de seus usuários bloqueado.",
    )
    observacoes = models.TextField("Observações", blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Canil"
        verbose_name_plural = "Canis"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def total_caes(self):
        return self.caes.count()

    def total_usuarios(self):
        return self.vinculos.filter(ativo=True).count()


class VinculoUsuario(models.Model):
    """Liga um usuário do sistema a um canil (cada usuário opera 1 canil).

    Superusuários (gestores gerais) não precisam de vínculo: enxergam
    todos os canis pelo painel de gestão.
    """

    PAPEL_CHOICES = [
        ("admin_canil", "Administrador do canil"),
        ("operador", "Operador"),
    ]

    usuario = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="vinculo_canil"
    )
    canil = models.ForeignKey(
        Canil, on_delete=models.CASCADE, related_name="vinculos"
    )
    papel = models.CharField("Papel", max_length=20, choices=PAPEL_CHOICES, default="operador")
    ativo = models.BooleanField("Ativo", default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vínculo de usuário"
        verbose_name_plural = "Vínculos de usuários"

    def __str__(self):
        return f"{self.usuario.username} - {self.canil.nome}"
