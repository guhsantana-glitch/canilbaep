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
        textColor=colors.HexColor("#33513f")
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
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#33513f")),
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
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#33513f")),
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
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#33513f")),
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
