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
    """Gera um PDF A5 para fixar na porta do box do cão."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A5,
        topMargin=1.2 * cm, bottomMargin=1.2 * cm,
        leftMargin=1.2 * cm, rightMargin=1.2 * cm,
    )
    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        "Titulo", parent=styles["Title"], alignment=TA_CENTER, fontSize=20
    )
    subtitulo_style = ParagraphStyle(
        "Subtitulo", parent=styles["Normal"], alignment=TA_CENTER, fontSize=10,
        textColor=colors.HexColor("#2f8fc4")
    )
    label_style = ParagraphStyle("Label", parent=styles["Normal"], fontSize=12, leading=18)

    story = []
    _cabecalho_com_logo(story)
    story.append(Paragraph("10° BAEP - CANIL", subtitulo_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph(cao.nome.upper(), titulo_style))
    story.append(Spacer(1, 10))

    if cao.foto:
        try:
            story.append(Image(cao.foto.path, width=6 * cm, height=6 * cm))
            story.append(Spacer(1, 10))
        except Exception:
            pass

    dados = [
        ["Raça:", cao.raca],
        ["Sexo:", cao.get_sexo_display()],
        ["Nascimento:", cao.data_nascimento.strftime("%d/%m/%Y") if cao.data_nascimento else "-"],
        ["Ingresso no plantel:", cao.data_ingresso.strftime("%d/%m/%Y")],
        ["Situação:", cao.get_status_display()],
        ["Box:", cao.box or "-"],
        ["Condutor atual:", cao.condutor_atual.nome if cao.condutor_atual else "-"],
        ["Microchip:", cao.microchip or "-"],
        ["Patrimônio:", cao.patrimonio or "-"],
    ]
    tabela = Table(dados, colWidths=[5 * cm, 6 * cm])
    tabela.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
    ]))
    story.append(tabela)

    if cao.observacoes:
        story.append(Spacer(1, 12))
        story.append(Paragraph("<b>Observações:</b>", label_style))
        story.append(Paragraph(cao.observacoes, styles["Normal"]))

    doc.build(story)
    buffer.seek(0)
    return buffer


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
        dados = [["Tipo", "Aplicação", "Próxima dose", "Veterinário"]]
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
