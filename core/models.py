from django.db import models
from django.contrib.auth.models import User


class Veterinario(models.Model):
    canil = models.ForeignKey(
        "canis.Canil", on_delete=models.CASCADE, related_name="veterinarios",
        verbose_name="Canil", null=True, blank=True,
    )
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
    canil = models.ForeignKey(
        "canis.Canil", on_delete=models.CASCADE, related_name="tipos_vacina",
        verbose_name="Canil", null=True, blank=True,
    )
    nome = models.CharField("Nome da vacina", max_length=100)
    nome_comercial = models.CharField("Nome comercial", max_length=100, blank=True)
    fabricante = models.CharField("Fabricante", max_length=100, blank=True)
    partida = models.CharField("Partida", max_length=60, blank=True)
    data_fabricacao = models.DateField("Data de fabricação", null=True, blank=True)
    data_validade = models.DateField("Data de validade", null=True, blank=True)
    descricao = models.CharField("Descrição", max_length=200, blank=True)
    ativo = models.BooleanField("Ativo", default=True)

    class Meta:
        verbose_name = "Tipo de vacina"
        verbose_name_plural = "Tipos de vacina"
        ordering = ["nome"]
        constraints = [
            models.UniqueConstraint(fields=["canil", "nome"], name="uniq_tipovacina_canil_nome")
        ]

    def __str__(self):
        return self.nome


class Condutor(models.Model):
    canil = models.ForeignKey(
        "canis.Canil", on_delete=models.CASCADE, related_name="condutores",
        verbose_name="Canil", null=True, blank=True,
    )
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

    canil = models.ForeignKey(
        "canis.Canil", on_delete=models.CASCADE, related_name="caes",
        verbose_name="Canil", null=True, blank=True,
    )
    nome = models.CharField("Nome", max_length=100)
    raca = models.CharField("Raça", max_length=80)
    sexo = models.CharField("Sexo", max_length=1, choices=Sexo.choices)
    microchip = models.CharField("Nº microchip", max_length=40, blank=True)
    data_nascimento = models.DateField("Data de nascimento", null=True, blank=True)
    data_ingresso = models.DateField("Data de ingresso no plantel")
    status = models.CharField("Situação", max_length=20, choices=Status.choices, default=Status.ATIVO)
    condutor_atual = models.ForeignKey(
        Condutor, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="caes", verbose_name="Condutor atual / Adestrador"
    )
    box = models.CharField("Box / Baia", max_length=30, blank=True)
    foto = models.ImageField("Foto", upload_to="caes/fotos/", blank=True, null=True)
    origem = models.CharField("Origem (doação, compra, nascido no canil...)", max_length=150, blank=True)
    # Campos da Ficha Sanitária oficial do 10º BAEP
    especialidade = models.CharField(
        "Especialidade (ex: Dupla Função, Faro, Guarda...)", max_length=100, blank=True
    )
    numero_cro_cpr = models.CharField("Nº CRO/CPR (ex: CBKC: BRC/18/00765)", max_length=100, blank=True)
    registro_sbcpa = models.CharField("Registro SBCPA (ex: CBPA-SP/21697)", max_length=100, blank=True)
    patrimonio = models.CharField("Patrimônio (nº patrimonial PMESP)", max_length=60, blank=True)
    observacoes = models.TextField("Observações gerais / Outras observações", blank=True)
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

    @property
    def tem_foto(self):
        """True só se há foto cadastrada E o arquivo realmente existe
        (evita quadro em branco quando o arquivo foi perdido)."""
        if not self.foto:
            return False
        try:
            return self.foto.storage.exists(self.foto.name)
        except Exception:
            return False

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
        AT_VACINA = "AT_VACINA", "Atestado de vacinação"
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


class Vermifugacao(models.Model):
    """Quadro de vermifugação da Ficha Sanitária."""

    cao = models.ForeignKey(Cao, on_delete=models.CASCADE, related_name="vermifugacoes")
    vermifugo = models.CharField("Vermífugo (produto)", max_length=100)
    data_aplicacao = models.DateField("Data de aplicação")
    veterinario = models.ForeignKey(
        Veterinario, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="vermifugacoes", verbose_name="Veterinário responsável"
    )
    lote = models.CharField("Lote", max_length=60, blank=True)
    observacoes = models.TextField("Observações", blank=True)

    class Meta:
        verbose_name = "Vermifugação"
        verbose_name_plural = "Vermifugações"
        ordering = ["-data_aplicacao"]

    def __str__(self):
        return f"{self.vermifugo} - {self.cao.nome} ({self.data_aplicacao})"


class Ectoparasita(models.Model):
    """Controle de ectoparasitas da Ficha Sanitária (procedimento + data)."""

    cao = models.ForeignKey(Cao, on_delete=models.CASCADE, related_name="ectoparasitas")
    procedimento = models.CharField("Procedimento (produto aplicado)", max_length=150)
    data_aplicacao = models.DateField("Aplicação em")
    veterinario = models.ForeignKey(
        Veterinario, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="ectoparasitas", verbose_name="Veterinário responsável"
    )
    observacoes = models.TextField("Observações", blank=True)

    class Meta:
        verbose_name = "Controle de ectoparasita"
        verbose_name_plural = "Controle de ectoparasitas"
        ordering = ["-data_aplicacao"]

    def __str__(self):
        return f"{self.procedimento} - {self.cao.nome} ({self.data_aplicacao})"


class OcorrenciaSaude(models.Model):
    """Alteração da saúde do animal: anormalidade, data, vet e medicamento."""

    cao = models.ForeignKey(Cao, on_delete=models.CASCADE, related_name="ocorrencias_saude")
    anormalidade = models.CharField("Anormalidade", max_length=200)
    data = models.DateField("Data")
    veterinario = models.ForeignKey(
        Veterinario, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="ocorrencias_saude", verbose_name="Méd. veterinário"
    )
    medicamento = models.CharField("Medicamento", max_length=200, blank=True)
    observacoes = models.TextField("Observações", blank=True)

    class Meta:
        verbose_name = "Ocorrência de saúde"
        verbose_name_plural = "Ocorrências de saúde"
        ordering = ["-data"]

    def __str__(self):
        return f"{self.anormalidade} - {self.cao.nome} ({self.data})"


class VisitaTecnica(models.Model):
    """Visita técnica do médico veterinário (5º BPChoque / CPChq)."""

    cao = models.ForeignKey(Cao, on_delete=models.CASCADE, related_name="visitas_tecnicas")
    data = models.DateField("Data da visita")
    medico_veterinario = models.CharField("Post/Grad + nome do méd. veterinário", max_length=150)
    observacoes = models.TextField("Observações da visita", blank=True)

    class Meta:
        verbose_name = "Visita técnica veterinária"
        verbose_name_plural = "Visitas técnicas veterinárias"
        ordering = ["-data"]

    def __str__(self):
        return f"Visita {self.data} - {self.cao.nome}"


class OcorrenciaPolicial(models.Model):
    """Ocorrência operacional com emprego de cão farejador / patrulha.

    Tipificação PMESP: F01 (tráfico de drogas), J09 (arma de fogo),
    G01 (captura de procurado).
    """

    class Tipo(models.TextChoices):
        F01 = "F01", "F01 — Tráfico de drogas"
        J09 = "J09", "J09 — Arma de fogo"
        G01 = "G01", "G01 — Captura de procurado"

    class DrogaTipo(models.TextChoices):
        NA = "NA", "Não se aplica / nenhuma"
        MACONHA = "MACONHA", "Maconha"
        COCAINA = "COCAINA", "Cocaína"
        CRACK = "CRACK", "Crack"
        ECSTASY = "ECSTASY", "Ecstasy / sintéticas"
        HAXIXE = "HAXIXE", "Haxixe / skunk"
        OUTRA = "OUTRA", "Outra (descrever nas observações)"

    class DrogaUnidade(models.TextChoices):
        G = "G", "g (gramas)"
        KG = "KG", "kg (quilos)"
        UN = "UN", "un (porções/pinos/pedras)"

    cao = models.ForeignKey(
        Cao, on_delete=models.CASCADE, related_name="ocorrencias_policiais",
        verbose_name="Cão empregado",
    )
    data = models.DateField("Data da ocorrência")
    tipo = models.CharField("Tipo de ocorrência", max_length=3, choices=Tipo.choices)
    numero_bo = models.CharField("Nº do BO / RDO", max_length=40, blank=True)
    local = models.CharField("Local da ocorrência", max_length=200, blank=True)
    condutor = models.ForeignKey(
        Condutor, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="ocorrencias_policiais", verbose_name="Condutor / responsável pelo cão",
    )
    droga_tipo = models.CharField(
        "Tipo de droga apreendida", max_length=10,
        choices=DrogaTipo.choices, default=DrogaTipo.NA,
    )
    droga_quantidade = models.DecimalField(
        "Quantidade de droga", max_digits=10, decimal_places=3,
        null=True, blank=True,
    )
    droga_unidade = models.CharField(
        "Unidade da droga", max_length=2,
        choices=DrogaUnidade.choices, default=DrogaUnidade.G,
    )
    qtd_armas = models.PositiveIntegerField("Quantidade de armas apreendidas", default=0)
    descricao_armas = models.CharField(
        "Descrição das armas (tipo/calibre/modelo)", max_length=250, blank=True,
    )
    qtd_procurados = models.PositiveIntegerField("Procurados capturados", default=0)
    observacoes = models.TextField("Observações / detalhes da ocorrência", blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ocorrência policial"
        verbose_name_plural = "Ocorrências policiais"
        ordering = ["-data", "-id"]

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.cao.nome} ({self.data})"

    @property
    def resumo_apreensao(self):
        partes = []
        if self.droga_tipo != self.DrogaTipo.NA and self.droga_quantidade:
            partes.append(
                f"{self.get_droga_tipo_display()}: {self.droga_quantidade} {self.get_droga_unidade_display()}"
            )
        if self.qtd_armas:
            partes.append(f"{self.qtd_armas} arma(s)")
        if self.qtd_procurados:
            partes.append(f"{self.qtd_procurados} procurado(s)")
        return " · ".join(partes) if partes else "-"
