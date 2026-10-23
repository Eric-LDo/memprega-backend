from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether
from app.schemas import ResumeData


def render_pdf(data: ResumeData) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=44, leftMargin=44,
                            topMargin=40, bottomMargin=42, title=f"Currículo - {data.name}", author=data.name)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Person", fontName="Helvetica-Bold", fontSize=23, leading=28, textColor=colors.HexColor("#153e42"), spaceAfter=6))
    styles.add(ParagraphStyle(name="Section", fontName="Helvetica-Bold", fontSize=11, leading=15, textColor=colors.HexColor("#176b61"), spaceBefore=17, spaceAfter=8, keepWithNext=True))
    styles.add(ParagraphStyle(name="Copy", fontSize=10, leading=15, alignment=TA_LEFT, spaceAfter=5, splitLongWords=True))
    story = []

    def p(text, style="Copy"):
        return Paragraph(escape(text).replace("\n", "<br/>"), styles[style])

    def period(item):
        def fmt(value):
            return "/".join(reversed(value.split("-")))
        return f"{fmt(item.start)} — {'Atual' if item.current else fmt(item.end)}"

    story.extend([p(data.name, "Person"), p(data.title), p(" | ".join([data.email, data.phone, data.city]))])
    for link in (data.linkedin, data.portfolio):
        if link:
            story.append(p(link))
    if data.summary:
        story.extend([p("RESUMO PROFISSIONAL", "Section"), p(data.summary)])
    if data.experiences:
        story.append(p("EXPERIÊNCIA PROFISSIONAL", "Section"))
        for item in data.experiences:
            story.append(KeepTogether([p(item.role, "Heading3"), p(f"{item.company} | {period(item)}")]))
            story.extend([p(item.description), Spacer(1, 6)])
    if data.education:
        story.append(p("FORMAÇÃO ACADÊMICA", "Section"))
        for item in data.education:
            story.append(KeepTogether([p(item.course, "Heading3"), p(f"{item.institution} | {item.level}"), p(period(item))]))
    if data.skills:
        story.extend([p("HABILIDADES", "Section"), p(" • ".join(data.skills))])
    if data.languages:
        story.extend([p("IDIOMAS", "Section"), p(" • ".join(f"{v.name}: {v.level}" for v in data.languages))])

    def footer(canvas, document):
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#687779"))
        canvas.drawRightString(A4[0] - 44, 24, str(document.page))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
