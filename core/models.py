from django.db import models
from django.contrib.auth.models import User


class Veterinario(models.Model):
    nome = models.CharField("Nome completo", max_length=150)
    crmv = models.CharField("CRMV (registro profissional)", max_length=30, blank=True)
    telefone = models.CharField("Telefone", max_length=20, blank=True)
    email = models.EmailField("E-mail", blank=True)
    ativo = models.BooleanField("Ativo", default=True)
    observacoes = models.TextField("Observações", blank=True)

    class Meta:
        verbose_name = "Veterinário"
        verbose_name_plural = "Veterinários"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class TipoVacina(models.Model):
    nome = models.CharField("Nome da vacina", max_length=100, unique=True)
    descricao = models.CharField("Descrição", max_length=200, blank=True)
    ativo = models.BooleanField("Ativo", default=True)

    class Meta:
        verbose_name = "Tipo de vacina"
        verbose_name_plural = "Tipos de vacina"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Condutor(models.Model):
    nome = models.CharField("Nome completo", max_length=150)
    matricula = models.CharField("Matrícula", max_length=30, unique=True)
    posto_graduacao = models.CharField("Posto/Graduação", max_length=60, blank=True)
    telefone = models.CharField("Telefone", max_length=20, blank=True)
    ativo = models.BooleanField("Ativo", default=True)
    usuario = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="condutor", verbose_name="Usuário do sistema"
    )
    observacoes = models.TextField("Observações", blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Condutor"
        verbose_name_plural = "Condutores"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.matricula})"


class Cao(models.Model):
    class Sexo(models.TextChoices):
        MACHO = "M", "Macho"
        FEMEA = "F", "Fêmea"

    class Status(models.TextChoices):
        ATIVO = "ATIVO", "Ativo no plantel"
        TREINAMENTO = "TREINAMENTO", "Em treinamento"
        BAIXADO = "BAIXADO", "Baixado / Fora de serviço"
        OBITO = "OBITO", "Óbito"

    nome = models.CharField("Nome", max_length=100)
    raca = models.CharField("Raça", max_length=80)
    sexo = models.CharField("Sexo", max_length=1, choices=Sexo.choices)
    microchip = models.CharField("Nº microchip", max_length=40, blank=True)
    data_nascimento = models.DateField("Data de nascimento", null=True, blank=True)
    data_ingresso = models.DateField("Data de ingresso no plantel")
    status = models.CharField("Situação", max_length=20, choices=Status.choices, default=Status.ATIVO)
    condutor_atual = models.ForeignKey(
        Condutor, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="caes", verbose_name="Condutor atual"
    )
    box = models.CharField("Box / Baia", max_length=30, blank=True)
    foto = models.ImageField("Foto", upload_to="caes/fotos/", blank=True, null=True)
    origem = models.CharField("Origem (doação, compra, nascido no canil...)", max_length=150, blank=True)
    observacoes = models.TextField("Observações gerais", blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cão"
        verbose_name_plural = "Cães"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def peso_atual(self):
        ultima = self.pesagens.order_by("-data").first()
        return ultima.peso_kg if ultima else None

    def idade_aproximada(self):
        if not self.data_nascimento:
            return None
        from datetime import date
        hoje = date.today()
        anos = hoje.year - self.data_nascimento.year - (
            (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day)
        )
        return anos


class Vacina(models.Model):
    cao = models.ForeignKey(Cao, on_delete=models.CASCADE, related_name="vacinas")
    tipo = models.ForeignKey(
        TipoVacina, on_delete=models.PROTECT, related_name="aplicacoes", verbose_name="Tipo de vacina"
    )
    data_aplicacao = models.DateField("Data de aplicação")
    data_proxima_dose = models.DateField("Próxima dose", null=True, blank=True)
    veterinario = models.ForeignKey(
        Veterinario, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="vacinas_aplicadas", verbose_name="Veterinário responsável"
    )
    lote = models.CharField("Lote", max_length=60, blank=True)
    observacoes = models.TextField("Observações", blank=True)

    class Meta:
        verbose_name = "Vacina"
        verbose_name_plural = "Vacinas"
        ordering = ["-data_aplicacao"]

    def __str__(self):
        return f"{self.tipo} - {self.cao.nome} ({self.data_aplicacao})"


class Medicamento(models.Model):
    cao = models.ForeignKey(Cao, on_delete=models.CASCADE, related_name="medicamentos")
    nome = models.CharField("Medicamento", max_length=100)
    dosagem = models.CharField("Dosagem", max_length=100)
    motivo = models.CharField("Motivo / diagnóstico", max_length=200, blank=True)
    data_inicio = models.DateField("Início do tratamento")
    data_fim = models.DateField("Fim do tratamento", null=True, blank=True)
    veterinario = models.ForeignKey(
        Veterinario, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="medicamentos_prescritos", verbose_name="Veterinário responsável"
    )
    observacoes = models.TextField("Observações", blank=True)

    class Meta:
        verbose_name = "Medicamento"
        verbose_name_plural = "Medicamentos"
        ordering = ["-data_inicio"]

    def __str__(self):
        return f"{self.nome} - {self.cao.nome}"


class Pesagem(models.Model):
    cao = models.ForeignKey(Cao, on_delete=models.CASCADE, related_name="pesagens")
    data = models.DateField("Data da pesagem")
    peso_kg = models.DecimalField("Peso (kg)", max_digits=5, decimal_places=2)
    observacoes = models.CharField("Observações", max_length=200, blank=True)

    class Meta:
        verbose_name = "Pesagem"
        verbose_name_plural = "Pesagens"
        ordering = ["-data"]
        unique_together = ("cao", "data")

    def __str__(self):
        return f"{self.cao.nome} - {self.data} - {self.peso_kg}kg"


class Treinamento(models.Model):
    class Etapa(models.TextChoices):
        FILHOTE = "FILHOTE", "Filhotagem / socialização"
        BASICO = "BASICO", "Obediência básica"
        FARO = "FARO", "Faro / detecção"
        DEFESA = "DEFESA", "Defesa / patrulhamento"
        REFORCO = "REFORCO", "Reciclagem / reforço"
        OUTRO = "OUTRO", "Outro"

    cao = models.ForeignKey(Cao, on_delete=models.CASCADE, related_name="treinamentos")
    data = models.DateField("Data")
    etapa = models.CharField("Etapa/Tipo", max_length=20, choices=Etapa.choices)
    descricao = models.TextField("Descrição do treinamento")
    resultado = models.CharField("Resultado/avaliação (texto)", max_length=200, blank=True)
    nota_avaliacao = models.DecimalField(
        "Nota de avaliação (0 a 10)", max_digits=4, decimal_places=1, null=True, blank=True
    )
    instrutor = models.CharField("Instrutor responsável", max_length=100, blank=True)

    class Meta:
        verbose_name = "Treinamento"
        verbose_name_plural = "Treinamentos"
        ordering = ["-data"]

    def __str__(self):
        return f"{self.get_etapa_display()} - {self.cao.nome} ({self.data})"


class Documento(models.Model):
    class Tipo(models.TextChoices):
        EXAME = "EXAME", "Resultado de exame"
        INGRESSO = "INGRESSO", "Documento de ingresso no plantel"
        LAUDO = "LAUDO", "Laudo veterinário"
        OUTRO = "OUTRO", "Outro"

    cao = models.ForeignKey(Cao, on_delete=models.CASCADE, related_name="documentos")
    tipo = models.CharField("Tipo de documento", max_length=20, choices=Tipo.choices)
    titulo = models.CharField("Título/descrição", max_length=150)
    arquivo = models.FileField("Arquivo", upload_to="caes/documentos/%Y/%m/")
    data_documento = models.DateField("Data do documento", null=True, blank=True)
    enviado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ["-enviado_em"]

    def __str__(self):
        return f"{self.titulo} - {self.cao.nome}"
