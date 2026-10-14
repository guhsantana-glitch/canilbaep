"""Geração de PDFs: ficha para porta do box e relatório mensal do cão."""

from io import BytesIO
from pathlib import Path
from reportlab.lib.pagesizes import A5, A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

# Coloque aqui o logotipo do canil (enviado pelo usuário) para que apareça
# automaticamente nos PDFs. Aceita .png ou .jpg. Se o arquivo não existir,
# o cabeçalho é gerado normalmente, apenas em texto.
BASE_DIR = Path(__file__).resolve().parent.parent
PASTA_LOGOS = BASE_DIR / "static" / "logos"
LOGO_CANIL = PASTA_LOGOS / "logo_canil.png"


def _cabecalho_com_logo(story):
    """Adiciona o logotipo do canil centralizado no topo, se existir."""
    from PIL import Image as PILImage

    if not LOGO_CANIL.exists():
        return
    try:
        largura_original, altura_original = PILImage.open(LOGO_CANIL).size
        altura_alvo = 3 * cm
        largura_alvo = altura_alvo * (largura_original / altura_original)
        imagem = Image(str(LOGO_CANIL), width=largura_alvo, height=altura_alvo)
        imagem.hAlign = "CENTER"
        story.append(imagem)
        story.append(Spacer(1, 6))
    except Exception:
        pass


def gerar_ficha_box(cao):
    """Ficha A5 para a porta do box — cabe em 1 página, nome nunca corta.

    Layout profissional: faixa institucional, nome com fonte adaptativa
    (quebra de linha + reduz conforme o tamanho), box em destaque, foto
    com proporção preservada e tabela compacta de dados.
    """
    from datetime import date
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A5,
        topMargin=0.9 * cm, bottomMargin=0.9 * cm,
        leftMargin=0.9 * cm, rightMargin=0.9 * cm,
        title=f"Box - {cao.nome}",
    )
    styles = getSampleStyleSheet()
    AZUL = colors.HexColor("#1a3a5f")
    CIANO = colors.HexColor("#2f8fc4")

    faixa = ParagraphStyle("BoxFaixa", parent=styles["Normal"], alignment=TA_CENTER,
                           fontSize=8, leading=10, textColor=CIANO, spaceAfter=2)
    # Nome com tamanho adaptativo para nunca cortar
    nome_txt = (cao.nome or "-").upper()
    if len(nome_txt) > 32:
        nome_size, nome_lead = 13, 15
    elif len(nome_txt) > 22:
        nome_size, nome_lead = 15, 17
    else:
        nome_size, nome_lead = 18, 20
    nome_style = ParagraphStyle("BoxNome", parent=styles["Title"], alignment=TA_CENTER,
                                fontSize=nome_size, leading=nome_lead, textColor=AZUL,
                                spaceBefore=2, spaceAfter=2)
    rotulo = ParagraphStyle("BoxRot", parent=styles["Normal"], fontSize=8.5, leading=11,
                            textColor=colors.HexColor("#555555"))
    valor = ParagraphStyle("BoxVal", parent=styles["Normal"], fontSize=9.5, leading=11.5)
    box_style = ParagraphStyle("BoxNum", parent=styles["Title"], alignment=TA_CENTER,
                               fontSize=16, leading=18, textColor=colors.white)
    rodape = ParagraphStyle("BoxRod", parent=styles["Normal"], alignment=TA_CENTER,
                            fontSize=6.5, leading=8, textColor=colors.HexColor("#888888"))

    story = []

    # Faixa institucional + logo compacto
    story.append(Paragraph("POLÍCIA MILITAR SP &nbsp;•&nbsp; 10º BAEP &nbsp;•&nbsp; CANIL — UNIDADE K-9 SUMARÉ", faixa))
    _cabecalho_com_logo_compacto(story, altura_cm=1.6)

    story.append(Paragraph(nome_txt, nome_style))

    # Box em destaque (etiqueta cheia)
    if cao.box:
        etiqueta = Table([[Paragraph(f"BOX &nbsp;{cao.box}", box_style)]], colWidths=[13 * cm])
        etiqueta.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), AZUL),
            ("ROUNDEDCORNERS", [4, 4, 4, 4]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(etiqueta)
        story.append(Spacer(1, 5))
    else:
        story.append(Spacer(1, 2))

    # Foto proporcional (nunca estoura a página)
    if cao.foto:
        try:
            from PIL import Image as PILImage
            with PILImage.open(cao.foto.path) as img:
                w0, h0 = img.size
            max_w, max_h = 5.2 * cm, 3.4 * cm
            escala = min(max_w / w0, max_h / h0)
            foto = Image(cao.foto.path, width=w0 * escala, height=h0 * escala)
            foto.hAlign = "CENTER"
            story.append(foto)
            story.append(Spacer(1, 5))
        except Exception:
            pass

    def L(t):
        return Paragraph(f"<b>{t}</b>", rotulo)

    def V(t):
        return Paragraph(t or "-", valor)

    nasc = cao.data_nascimento.strftime("%d/%m/%Y") if cao.data_nascimento else "-"
    if cao.data_nascimento and cao.idade_aproximada() is not None:
        nasc = f"{nasc} ({cao.idade_aproximada()}a)"
    linhas = [
        [L("Raça"), V(cao.raca), L("Sexo"), V(cao.get_sexo_display())],
        [L("Nascimento"), V(nasc), L("Ingresso"), V(cao.data_ingresso.strftime("%d/%m/%Y") if cao.data_ingresso else "-")],
        [L("Situação"), V(cao.get_status_display()), L("Peso"), V(f"{cao.peso_atual()} kg" if cao.peso_atual() else "-")],
        [L("Condutor"), V(cao.condutor_atual.nome if cao.condutor_atual else "-"), L("Especialidade"), V(cao.especialidade)],
        [L("Microchip"), V(cao.microchip), L("Patrimônio"), V(cao.patrimonio)],
        [L("CRO/CPR"), V(cao.numero_cro_cpr), L("SBCPA"), V(cao.registro_sbcpa)],
    ]
    larg = 13 * cm
    tabela = Table(linhas, colWidths=[2.6 * cm, 3.9 * cm, 2.6 * cm, 3.9 * cm])
    tabela.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d5dde5")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef3f7")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#eef3f7")),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
    ]))
    story.append(tabela)

    if cao.observacoes:
        obs = (cao.observacoes or "").strip().replace("\n", " ")
        if len(obs) > 220:
            obs = obs[:217] + "..."
        story.append(Spacer(1, 5))
        story.append(Paragraph(f"<b>Obs.:</b> {obs}", ParagraphStyle(
            "BoxObs", parent=styles["Normal"], fontSize=8, leading=10, alignment=TA_LEFT)))

    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"Emitido em {date.today().strftime('%d/%m/%Y')} &nbsp;•&nbsp; Ficha sanitária completa no sistema do Canil",
        rodape))

    doc.build(story)
    buffer.seek(0)
    return buffer


def _cabecalho_com_logo_compacto(story, altura_cm=1.6):
    """Logo compacto para a ficha de box (não empurra o conteúdo p/ 2ª página)."""
    from PIL import Image as PILImage

    if not LOGO_CANIL.exists():
        return
    try:
        with PILImage.open(LOGO_CANIL) as img:
            w0, h0 = img.size
        altura_alvo = altura_cm * cm
        imagem = Image(str(LOGO_CANIL), width=altura_alvo * (w0 / h0), height=altura_alvo)
        imagem.hAlign = "CENTER"
        story.append(imagem)
        story.append(Spacer(1, 3))
    except Exception:
        pass


def gerar_relatorio_mensal(cao, data_inicio, data_fim, pesagens, vacinas, medicamentos):
    """Gera um relatório PDF (A4) com pesagens, vacinas e medicamentos no período."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    story = []

    _cabecalho_com_logo(story)
    story.append(Paragraph("10° BAEP - Relatório Mensal do Canil", styles["Title"]))
    story.append(Paragraph(
        f"Cão: <b>{cao.nome}</b> &nbsp;|&nbsp; Período: "
        f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}",
        styles["Normal"]
    ))
    story.append(Spacer(1, 16))

    # Pesagens
    story.append(Paragraph("Pesagens", styles["Heading2"]))
    if pesagens:
        dados = [["Data", "Peso (kg)", "Observações"]]
        for p in pesagens:
            dados.append([p.data.strftime("%d/%m/%Y"), str(p.peso_kg), p.observacoes or "-"])
        t = Table(dados, colWidths=[3.5 * cm, 3.5 * cm, 8 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2f8fc4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("Sem registros de pesagem no período.", styles["Normal"]))
    story.append(Spacer(1, 16))

    # Vacinas
    story.append(Paragraph("Vacinas", styles["Heading2"]))
    if vacinas:
        dados = [["Tipo", "Vacinação em", "Revacinar em", "Veterinário"]]
        for v in vacinas:
            dados.append([
                v.tipo.nome, v.data_aplicacao.strftime("%d/%m/%Y"),
                v.data_proxima_dose.strftime("%d/%m/%Y") if v.data_proxima_dose else "-",
                v.veterinario.nome if v.veterinario else "-"
            ])
        t = Table(dados, colWidths=[4 * cm, 3.5 * cm, 3.5 * cm, 4 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2f8fc4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("Sem vacinas registradas no período.", styles["Normal"]))
    story.append(Spacer(1, 16))

    # Medicamentos
    story.append(Paragraph("Medicamentos", styles["Heading2"]))
    if medicamentos:
        dados = [["Medicamento", "Dosagem", "Início", "Fim", "Motivo"]]
        for m in medicamentos:
            dados.append([
                m.nome, m.dosagem, m.data_inicio.strftime("%d/%m/%Y"),
                m.data_fim.strftime("%d/%m/%Y") if m.data_fim else "-",
                m.motivo or "-"
            ])
        t = Table(dados, colWidths=[3.5 * cm, 3 * cm, 2.7 * cm, 2.7 * cm, 3.1 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2f8fc4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("Sem medicamentos registrados no período.", styles["Normal"]))

    doc.build(story)
    buffer.seek(0)
    return buffer


def gerar_relatorio_geral_mensal(data_inicio, data_fim, linhas, apenas_ativos):
    """Gera um PDF (A4, paisagem) com o resumo de todos os cães no período.

    `linhas` é uma lista de dicts com as chaves:
    nome, box, condutor, status, peso_atual, qtd_vacinas, qtd_medicamentos, qtd_treinamentos
    """
    from reportlab.lib.pagesizes import landscape

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    story = []

    _cabecalho_com_logo(story)
    titulo = "10° BAEP - Relatório Mensal Geral do Canil"
    if apenas_ativos:
        titulo += " (cães ativos no plantel)"
    story.append(Paragraph(titulo, styles["Title"]))
    story.append(Paragraph(
        f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}",
        styles["Normal"]
    ))
    story.append(Spacer(1, 14))

    cabecalho = ["Cão", "Box", "Condutor", "Situação", "Peso atual", "Vacinas no período", "Medicamentos no período", "Treinamentos no período"]
    dados = [cabecalho]
    for linha in linhas:
        dados.append([
            linha["nome"], linha["box"] or "-", linha["condutor"] or "-", linha["status"],
            f'{linha["peso_atual"]} kg' if linha["peso_atual"] is not None else "-",
            str(linha["qtd_vacinas"]), str(linha["qtd_medicamentos"]), str(linha["qtd_treinamentos"]),
        ])

    if len(dados) == 1:
        story.append(Paragraph("Nenhum cão encontrado para os filtros selecionados.", styles["Normal"]))
    else:
        t = Table(dados, repeatRows=1, colWidths=[3.2*cm, 2*cm, 3.8*cm, 2.6*cm, 2.4*cm, 3.3*cm, 3.7*cm, 3.3*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2f8fc4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(t)

    doc.build(story)
    buffer.seek(0)
    return buffer


def gerar_ficha_sanitaria(cao):
    """Ficha Sanitária individual do 10º BAEP (replica o papel oficial).

    Capa: cabeçalho + dados do cão + imunização + vermifugação + peso.
    Verso: ectoparasitas + ocorrências de saúde + visitas técnicas.
    Tabelas são completadas com linhas em branco para impressão.
    """
    from datetime import date

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=1.2 * cm, bottomMargin=1.2 * cm,
        leftMargin=1.2 * cm, rightMargin=1.2 * cm,
    )
    styles = getSampleStyleSheet()
    titulo = ParagraphStyle("FS_Titulo", parent=styles["Title"], fontSize=11, leading=13, alignment=TA_CENTER)
    secao = ParagraphStyle("FS_Secao", parent=styles["Heading3"], fontSize=10, leading=12, alignment=TA_CENTER, spaceBefore=8, spaceAfter=4)
    normal = styles["Normal"]
    normal.fontSize = 8
    normal.leading = 10
    cel = ParagraphStyle("FS_Cel", parent=normal, fontSize=8, leading=10)
    cab = ParagraphStyle("FS_Cab", parent=normal, fontSize=8, leading=10, textColor=colors.black)

    def p(txt):
        return Paragraph(txt or "-", cel)

    def fmt_data(d):
        return d.strftime("%d/%m/%Y") if d else "-"

    story = []
    _cabecalho_com_logo(story)
    story.append(Paragraph(
        "POLÍCIA MILITAR DO ESTADO DE SÃO PAULO<br/>"
        "COMANDO DE POLICIAMENTO DO INTERIOR – 9<br/>"
        "10º BATALHÃO DE AÇÕES ESPECIAIS DE POLÍCIA<br/>"
        f"BAEP - UNIDADE K-9 - SUMARÉ<br/>FICHA SANITÁRIA {date.today().year}",
        titulo,
    ))
    story.append(Spacer(1, 8))

    estilo_grade = TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ])

    dados_cao = [
        [Paragraph("<b>CÃO</b>", cab), p(cao.nome), Paragraph("<b>RAÇA</b>", cab), p(cao.raca)],
        [Paragraph("<b>SEXO</b>", cab), p(cao.get_sexo_display()), Paragraph("<b>INCL. NO PLANTEL</b>", cab), p(fmt_data(cao.data_ingresso))],
        [Paragraph("<b>D/NASC</b>", cab), p(fmt_data(cao.data_nascimento)), Paragraph("<b>ESPECIALIDADE</b>", cab), p(cao.especialidade)],
        [Paragraph("<b>Nº CRO/CPR</b>", cab), p(cao.numero_cro_cpr), Paragraph("<b>ADESTRADOR</b>", cab), p(cao.condutor_atual.nome if cao.condutor_atual else "")],
        [Paragraph("<b>CHIP</b>", cab), p(cao.microchip), Paragraph("<b>REGISTRO SBCPA</b>", cab), p(cao.registro_sbcpa)],
        [Paragraph("<b>PATRIMÔNIO</b>", cab), p(cao.patrimonio), Paragraph("<b>BOX / BAIA</b>", cab), p(cao.box)],
    ]
    t = Table(dados_cao, colWidths=[3 * cm, 6 * cm, 3.5 * cm, 5.5 * cm])
    t.setStyle(estilo_grade)
    story.append(t)

    def tabela_dupla(titulo_secao, cab_esq, cab_dir, linhas, minimo=8):
        story.append(Paragraph(titulo_secao, secao))
        meio = (len(linhas) + 1) // 2
        esq = linhas[:meio]
        dir_ = linhas[meio:]
        while len(esq) < (minimo + 1) // 2:
            esq.append(("", ""))
        while len(dir_) < minimo // 2:
            dir_.append(("", ""))
        dados = [[Paragraph(f"<b>{cab_esq}</b>", cab), Paragraph(f"<b>{cab_dir}</b>", cab),
                  Paragraph(f"<b>{cab_esq}</b>", cab), Paragraph(f"<b>{cab_dir}</b>", cab)]]
        for i in range(max(len(esq), len(dir_))):
            a = esq[i] if i < len(esq) else ("", "")
            b = dir_[i] if i < len(dir_) else ("", "")
            dados.append([p(a[0]), p(a[1]), p(b[0]), p(b[1])])
        tab = Table(dados, colWidths=[5 * cm, 4 * cm, 5 * cm, 4 * cm], repeatRows=1)
        tab.setStyle(estilo_grade)
        story.append(tab)

    vacinas = [(v.tipo.nome, fmt_data(v.data_aplicacao)) for v in cao.vacinas.select_related("tipo").order_by("data_aplicacao")]
    tabela_dupla("QUADRO DE IMUNIZAÇÃO", "NOME DA VACINA", "DATA APLICAÇÃO", vacinas)

    vermes = [(v.vermifugo, fmt_data(v.data_aplicacao)) for v in cao.vermifugacoes.order_by("data_aplicacao")]
    tabela_dupla("QUADRO DE VERMIFUGAÇÃO", "VERMÍFUGO", "DATA APLICAÇÃO", vermes)

    pesos = [(fmt_data(v.data), str(v.peso_kg).replace(".", ",")) for v in cao.pesagens.order_by("data")]
    tabela_dupla("CONTROLE DE PESO", "DATA DA PESAGEM", "PESO / Kg", pesos, minimo=6)

    ecto = [(e.procedimento, fmt_data(e.data_aplicacao)) for e in cao.ectoparasitas.order_by("data_aplicacao")]
    tabela_dupla("CONTROLE DE ECTOPARASITAS", "PROCEDIMENTO", "APLICAÇÃO EM", ecto, minimo=10)

    story.append(Paragraph("OBSERVAÇÕES", secao))
    story.append(Paragraph("Na alteração da saúde do animal, constar a anormalidade, data, médico veterinário e medicamento.", normal))
    story.append(Spacer(1, 4))
    ocorr = [
        (o.anormalidade, fmt_data(o.data),
         o.veterinario.nome if o.veterinario else "", o.medicamento or "")
        for o in cao.ocorrencias_saude.select_related("veterinario").order_by("data")
    ]
    while len(ocorr) < 6:
        ocorr.append(("", "", "", ""))
    dados = [[Paragraph("<b>ANORMALIDADE</b>", cab), Paragraph("<b>DATA</b>", cab),
              Paragraph("<b>MÉD. VETERINÁRIO</b>", cab), Paragraph("<b>MEDICAMENTO</b>", cab)]]
    for a, d, v, m in ocorr:
        dados.append([p(a), p(d), p(v), p(m)])
    tab = Table(dados, colWidths=[6 * cm, 3 * cm, 5 * cm, 4 * cm], repeatRows=1)
    tab.setStyle(estilo_grade)
    story.append(tab)

    story.append(Paragraph("OUTRAS OBSERVAÇÕES", secao))
    outras = (cao.observacoes or "").strip() or "—"
    tab = Table([[p(outras)]], colWidths=[18 * cm])
    tab.setStyle(estilo_grade)
    story.append(tab)

    story.append(Paragraph("VISITA TÉCNICA MÉDICO VETERINÁRIO 5º BPChoque", secao))
    visitas = [(fmt_data(v.data), v.medico_veterinario) for v in cao.visitas_tecnicas.order_by("data")]
    while len(visitas) < 5:
        visitas.append(("", ""))
    dados = [[Paragraph("<b>VISITA TÉCNICA MÉD. VETERINÁRIO CPChq</b>", cab),
              Paragraph("<b>DATA</b>", cab),
              Paragraph("<b>POST/GRAD/MÉDICO VETERINÁRIO</b>", cab)]]
    for d, v in visitas:
        dados.append([p("VISITA TÉCNICA MÉD. VETERINÁRIO CPChq"), p(d), p(v)])
    tab = Table(dados, colWidths=[7 * cm, 3.5 * cm, 7.5 * cm], repeatRows=1)
    tab.setStyle(estilo_grade)
    story.append(tab)

    story.append(Paragraph("TREINAMENTOS", secao))
    treinos = [
        (fmt_data(t.data), t.get_etapa_display(),
         str(t.nota_avaliacao).replace(".", ",") if t.nota_avaliacao is not None else "",
         t.instrutor or "", t.descricao or "")
        for t in cao.treinamentos.order_by("data")
    ]
    while len(treinos) < 6:
        treinos.append(("", "", "", "", ""))
    dados = [[Paragraph("<b>DATA</b>", cab), Paragraph("<b>ETAPA</b>", cab),
              Paragraph("<b>NOTA</b>", cab), Paragraph("<b>INSTRUTOR</b>", cab),
              Paragraph("<b>DESCRIÇÃO</b>", cab)]]
    for d, etapa, nota, instrutor, descricao in treinos:
        dados.append([p(d), p(etapa), p(nota), p(instrutor), p(descricao)])
    tab = Table(dados, colWidths=[2.5 * cm, 3.5 * cm, 1.8 * cm, 3.7 * cm, 6.5 * cm], repeatRows=1)
    tab.setStyle(estilo_grade)
    story.append(tab)

    story.append(Spacer(1, 12))
    rodape = ParagraphStyle("FS_Rodape", parent=normal, fontSize=7, leading=9, alignment=TA_CENTER)
    story.append(Paragraph(
        '"Nós, Policiais Militares, sob a proteção de Deus, estamos compromissados com a Defesa da Vida, '
        "da Integridade Física e da Dignidade da Pessoa Humana\"",
        rodape,
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer


def gerar_produtividade_mensal(canil_nome, mes, ano, cao_nome, ocorrencias, totais, por_tipo, drogas):
    """Relatório premium de produtividade mensal das ocorrências K-9 (A4).

    - `totais`: dict com total_ocorrencias, total_armas, total_procurados
    - `por_tipo`: dict {F01: n, J09: n, G01: n}
    - `drogas`: lista de dicts {droga_tipo, droga_unidade, total_qtd}
    """
    from datetime import date

    MESES_PT = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
    ]

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=1.4 * cm, bottomMargin=1.4 * cm,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        title=f"Produtividade {mes:02d}/{ano}",
    )
    styles = getSampleStyleSheet()
    AZUL = colors.HexColor("#0d3a5c")
    CIANO = colors.HexColor("#2f8fc4")
    CINZA_BG = colors.HexColor("#eef3f7")

    titulo = ParagraphStyle("Prod_Titulo", parent=styles["Title"], fontSize=16, leading=19,
                            textColor=AZUL, alignment=TA_CENTER, spaceAfter=2)
    subtitulo = ParagraphStyle("Prod_Sub", parent=styles["Normal"], fontSize=10, leading=13,
                               alignment=TA_CENTER, textColor=colors.HexColor("#3d5a6c"))
    kpi_num = ParagraphStyle("Prod_KPI_Num", parent=styles["Normal"], fontSize=18, leading=20,
                             alignment=TA_CENTER, textColor=colors.white)
    kpi_rot = ParagraphStyle("Prod_KPI_Rot", parent=styles["Normal"], fontSize=8, leading=10,
                             alignment=TA_CENTER, textColor=colors.white)
    secao = ParagraphStyle("Prod_Secao", parent=styles["Heading2"], fontSize=11, leading=14,
                           textColor=AZUL, spaceBefore=12, spaceAfter=6)
    cel = ParagraphStyle("Prod_Cel", parent=styles["Normal"], fontSize=8.5, leading=11)
    cel_c = ParagraphStyle("Prod_CelC", parent=cel, alignment=TA_CENTER)
    cab = ParagraphStyle("Prod_Cab", parent=cel, textColor=colors.white, alignment=TA_CENTER)
    rodape = ParagraphStyle("Prod_Rod", parent=styles["Normal"], fontSize=7, leading=9,
                            alignment=TA_CENTER, textColor=colors.HexColor("#888888"))

    nome_mes = MESES_PT[mes - 1] if 1 <= mes <= 12 else str(mes)

    story = []
    _cabecalho_com_logo(story)
    story.append(Paragraph("POLÍCIA MILITAR DO ESTADO DE SÃO PAULO &nbsp;•&nbsp; 10º BAEP &nbsp;•&nbsp; CANIL K-9", subtitulo))
    story.append(Spacer(1, 4))
    story.append(Paragraph("PRODUTIVIDADE MENSAL — EMPREGO DE CÃES", titulo))
    story.append(Paragraph(
        f"{canil_nome} &nbsp;•&nbsp; {nome_mes}/{ano} &nbsp;•&nbsp; Cão: <b>{cao_nome}</b>",
        subtitulo,
    ))
    story.append(Spacer(1, 10))

    # Faixa de KPIs
    def kpi(numero, rotulo):
        return [Paragraph(f"<b>{numero}</b>", kpi_num), Paragraph(rotulo.upper(), kpi_rot)]

    kpis = [[
        kpi(totais.get("total_ocorrencias", 0), "ocorrências"),
        kpi(por_tipo.get("F01", 0), "F01 tráfico"),
        kpi(por_tipo.get("J09", 0), "J09 arma"),
        kpi(por_tipo.get("G01", 0), "G01 procurado"),
    ], [
        kpi(totais.get("total_armas", 0) or 0, "armas"),
        kpi(totais.get("total_procurados", 0) or 0, "procurados"),
        kpi(len(drogas), "tipos droga"),
        kpi(totais.get("total_ocorrencias", 0), "lançamentos"),
    ]]
    # Simplifica: primeira linha com 4 KPIs principais
    faixa = Table([[
        Paragraph(f"<b>{totais.get('total_ocorrencias', 0)}</b>", kpi_num),
        Paragraph(f"<b>{por_tipo.get('F01', 0)}</b>", kpi_num),
        Paragraph(f"<b>{por_tipo.get('J09', 0)}</b>", kpi_num),
        Paragraph(f"<b>{por_tipo.get('G01', 0)}</b>", kpi_num),
    ], [
        Paragraph("OCORRÊNCIAS", kpi_rot), Paragraph("F01 TRÁFICO", kpi_rot),
        Paragraph("J09 ARMA", kpi_rot), Paragraph("G01 PROCURADO", kpi_rot),
    ], [
        Paragraph(f"<b>{totais.get('total_armas', 0) or 0}</b>", kpi_num),
        Paragraph(f"<b>{totais.get('total_procurados', 0) or 0}</b>", kpi_num),
        Paragraph(f"<b>{len(drogas)}</b>", kpi_num),
        Paragraph(f"<b>{totais.get('total_ocorrencias', 0)}</b>", kpi_num),
    ], [
        Paragraph("ARMAS APREEND.", kpi_rot), Paragraph("PROCURADOS", kpi_rot),
        Paragraph("TIPOS DROGA", kpi_rot), Paragraph("LANÇAMENTOS", kpi_rot),
    ]], colWidths=[4.2 * cm] * 4)
    faixa.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), AZUL),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 1), (-1, 1), 0.5, colors.HexColor("#ffffff55")),
    ]))
    story.append(faixa)
    story.append(Spacer(1, 6))

    def tabela_padrao(cabecalho, linhas, larguras):
        dados = [[Paragraph(f"<b>{c}</b>", cab) for c in cabecalho]]
        for linha in linhas:
            dados.append([Paragraph(str(v), cel_c if i > 0 else cel) for i, v in enumerate(linha)])
        t = Table(dados, colWidths=larguras, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), CIANO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d5dde5")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_BG]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ]))
        return t

    # Drogas apreendidas
    story.append(Paragraph("Drogas apreendidas no mês", secao))
    if drogas:
        story.append(tabela_padrao(
            ["Tipo de droga", "Quantidade", "Unidade"],
            [[d["droga_tipo_display"], str(d["total_qtd"]).replace(".", ","), d["droga_unidade_display"]] for d in drogas],
            [7 * cm, 5 * cm, 5 * cm],
        ))
    else:
        story.append(Paragraph("Sem apreensão de drogas no período.", styles["Normal"]))

    # Detalhamento das ocorrências
    story.append(Paragraph("Detalhamento das ocorrências", secao))
    if ocorrencias:
        linhas = []
        for o in ocorrencias:
            detalhe = []
            if o.droga_tipo != "NA" and o.droga_quantidade:
                detalhe.append(f"{o.get_droga_tipo_display()}: {str(o.droga_quantidade).replace('.', ',')} {o.get_droga_unidade_display()}")
            if o.qtd_armas:
                detalhe.append(f"{o.qtd_armas} arma(s){' — ' + o.descricao_armas if o.descricao_armas else ''}")
            if o.qtd_procurados:
                detalhe.append(f"{o.qtd_procurados} procurado(s)")
            linhas.append([
                o.data.strftime("%d/%m"),
                o.cao.nome,
                o.get_tipo_display().split(" — ")[0],
                o.prefixo_viatura or "-",
                o.numero_bo or "-",
                " · ".join(detalhe) if detalhe else "-",
            ])
        story.append(tabela_padrao(
            ["Data", "Cão", "Tipo", "Vtr", "BO", "Apreensões"],
            linhas,
            [1.8 * cm, 2.8 * cm, 1.8 * cm, 2.0 * cm, 2.8 * cm, 5.8 * cm],
        ))
    else:
        story.append(Paragraph("Sem ocorrências lançadas para o filtro selecionado.", styles["Normal"]))

    story.append(Spacer(1, 18))
    story.append(Paragraph(
        f"Emitido em {date.today().strftime('%d/%m/%Y')} pelo Sistema de Gestão do Canil &nbsp;•&nbsp; {canil_nome}",
        rodape,
    ))
    story.append(Spacer(1, 22))
    story.append(Table([
        [Paragraph("___________________________", cel_c), Paragraph("___________________________", cel_c)],
        [Paragraph("Comandante do Canil", cel_c), Paragraph("Responsável pela produtividade", cel_c)],
    ], colWidths=[8.5 * cm, 8.5 * cm]))

    doc.build(story)
    buffer.seek(0)
    return buffer
