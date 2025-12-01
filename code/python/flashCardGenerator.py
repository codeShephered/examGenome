import json
import math
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.pdfencrypt import StandardEncryption

JSON_FILE = "longDivFlashCard.json"
ICON_PATH = "examGenome.png"
OUTPUT_PREFIX = "examGenome_flashCard_longDivision"

# ------------------------------------------------------------
# Watermark
# ------------------------------------------------------------
def draw_watermark_and_background(canvas, doc):
    page_width, page_height = A4
    canvas.saveState()

    try:
        start_y = 680
        gap = 60
        canvas.setFillAlpha(0.15)

        for i in range(10):
            try:
                canvas.drawImage(
                    ICON_PATH,
                    page_width/2 - 15,
                    start_y - (i * gap),
                    width=20,
                    height=20,
                    mask="auto",
                    preserveAspectRatio=True,
                    anchor="c"
                )
            except:
                pass
    except:
        pass

    canvas.restoreState()

# ------------------------------------------------------------
# Generator
# ------------------------------------------------------------
def generate_flashcards(json_data):

    batch_size = 10
    total_batches = math.ceil(len(json_data) / batch_size)
    styles = getSampleStyleSheet()

    # 🔥 Reduced font size so text never spills into other columns
    q_style = ParagraphStyle(
        'QStyle',
        parent=styles['Normal'],
        fontSize=10,             # reduced from 12 → 10
        textColor=colors.black,
        leading=12,
        wordWrap='LTR'
    )

    a_style = ParagraphStyle(
        'AStyle',
        parent=styles['Normal'],
        fontSize=11,              # slightly smaller for long answers
        textColor=colors.black,
        leading=11,
        wordWrap='LTR'
    )

    centered_heading4 = ParagraphStyle(
        name='CenteredHeading4',
        parent=styles['Heading4'],
        alignment=1  # 1 for Center
    )

    for i in range(total_batches):

        filename = f"{OUTPUT_PREFIX}-{i+1}.pdf"

        start_idx = i * batch_size
        end_idx = start_idx + batch_size
        batch_data = json_data[start_idx:end_idx]

        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=10, leftMargin=10, topMargin=10, bottomMargin=10
        )

        elements = []

        # ----------------------------------------------------
        # ICON ABOVE TITLE
        # ----------------------------------------------------
        try:
            logo = Image(ICON_PATH, width=70, height=70)
            logo.hAlign = 'CENTER'
            elements.append(logo)
            elements.append(Spacer(1, 10))
        except:
            pass

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------
        title = Paragraph("<b>examGenome Flashcard on Long Division</b>", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 20))

        # ----------------------------------------------------
        # TABLE: Questions + Answers in same row
        # ----------------------------------------------------
        table_data = []

        table_data.append([
            Paragraph("<b>No.</b>", centered_heading4),
            Paragraph("<b>Question</b>", centered_heading4),
            Paragraph("<b>Answer</b>", centered_heading4)
        ])

        for row_index, item in enumerate(batch_data):
            q_no = row_index + 1

            question = Paragraph(item.get("question", ""), q_style)
            answer = Paragraph(item.get("answer", ""), a_style)

            table_data.append([str(q_no), question, answer])

        # ----------------------------------------------------
        # COLUMN WIDTH ADJUSTED
        # No. → 40
        # Question → 300
        # Answer → 170  (increased from 120)
        # ----------------------------------------------------
        t = Table(
            table_data,
            colWidths=[40, 300, 170],   # 🟢 Increased Answer column width
            rowHeights=[50, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60],      
            repeatRows=1
        )

        tbl_style = TableStyle([
            ('GRID', (0,0), (-1,-1), 0.4, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (0,0), (0,-1), 'CENTER'),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('BACKGROUND', (0,0), (-1,0), colors.Color(0.85, 0.85, 0.88)),
            ('NOSPLIT', (0,0), (-1,-1)),
        ])

        # Alternating row background
        for r in range(1, len(table_data)):
            if r % 2 == 0:
                tbl_style.add('BACKGROUND', (0, r), (-1, r), colors.Color(0.96, 0.96, 0.96))
            else:
                tbl_style.add('BACKGROUND', (0, r), (-1, r), colors.Color(0.985, 0.985, 0.985))

        t.setStyle(tbl_style)
        elements.append(t)

        # ----------------------------------------------------
        # BUILD DOCUMENT
        # ----------------------------------------------------
        doc.build(
            elements,
            onFirstPage=draw_watermark_and_background,
            onLaterPages=draw_watermark_and_background
        )

        print(f"✔ Generated: {filename}")

# ------------------------------------------------------------
# EXECUTION
# ------------------------------------------------------------
if __name__ == "__main__":
    with open(JSON_FILE, "r") as f:
        data = json.load(f)
        generate_flashcards(data)
