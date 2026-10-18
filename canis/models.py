from django.db import models
from django.contrib.auth.models import User


class Unidade(models.Model):
    """Batalhão/Unidade da PM que terá acesso ao sistema (ex: 10º BAEP).

    Cada unidade pode ter um ou mais canis setoriais.
    """

    nome = models.CharField("Nome da unidade (ex: 10º BAEP)", max_length=150, unique=True)
    cidade_sede = models.CharField("Cidade sede", max_length=100, blank=True)
    comandante = models.CharField("Comandante responsável", max_length=150, blank=True)
    telefone = models.CharField("Telefone", max_length=20, blank=True)
    email = models.EmailField("E-mail", blank=True)
    ativo = models.BooleanField(
        "Ativa", default=True,
        help_text="Unidade desativada bloqueia a criação de novos canis nela.",
    )
    observacoes = models.TextField("Observações", blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Unidade"
        verbose_name_plural = "Unidades"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Canil(models.Model):
    """Cada canil setorial da PM que utiliza o sistema (tenant)."""

    unidade = models.ForeignKey(
        Unidade, on_delete=models.PROTECT, related_name="canis",
        verbose_name="Unidade",
    )
    nome = models.CharField("Nome do canil", max_length=150)
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


class Pelotao(models.Model):
    """Pelotão dentro de um canil (ex: 1º Pelotão, 2º Pelotão).

    Usuários operadores só enxergam cães e ocorrências do seu pelotão.
    O pelotão de um cão é derivado do seu condutor atual.
    """

    canil = models.ForeignKey(
        Canil, on_delete=models.CASCADE, related_name="pelotoes",
        verbose_name="Canil",
    )
    nome = models.CharField("Nome do pelotão (ex: 1º Pelotão)", max_length=80)
    ativo = models.BooleanField(
        "Ativo", default=True,
        help_text="Pelotão desativado não pode ser selecionado em novos cadastros.",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pelotão"
        verbose_name_plural = "Pelotões"
        ordering = ["nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["canil", "nome"], name="uniq_pelotao_canil_nome"
            ),
        ]

    def __str__(self):
        return f"{self.nome} ({self.canil.nome})"


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
    pelotao = models.ForeignKey(
        Pelotao, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="vinculos", verbose_name="Pelotão",
        help_text="Operadores só enxergam cães e ocorrências do seu pelotão. "
                  "Administradores do canil veem todos.",
    )
    ativo = models.BooleanField("Ativo", default=True)
    senha_temporaria = models.BooleanField(
        "Precisa trocar a senha no próximo login", default=False,
        help_text="Marcado automaticamente quando a senha é definida na criação ou redefinição.",
    )
    senha_temporaria_em = models.DateTimeField(
        "Senha temporária emitida em", null=True, blank=True,
        help_text="Início do prazo de 7 dias para a troca. Vínculos antigos sem data usam a data de criação.",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vínculo de usuário"
        verbose_name_plural = "Vínculos de usuários"

    def __str__(self):
        return f"{self.usuario.username} - {self.canil.nome}"
