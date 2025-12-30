import json
import math
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Configuration
JSON_FILE = "../../jsons/cheatsheets/src/stats_and_probability_cheatSheet.json"
ICON_PATH = "examGenome.png"
OUTPUT_PREFIX = "examGenome_cheatSheet_rstats_and_probability"

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

    # Style for the combined content column
    content_style = ParagraphStyle(
        'ContentStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        leading=14,  # Increased leading for better readability between lines
        wordWrap='LTR'
    )

    centered_heading = ParagraphStyle(
        name='CenteredHeading',
        parent=styles['Heading4'],
        alignment=1 
    )

    for i in range(total_batches):
        # Unique filename for each batch if you want separate files, 
        # or keep the same if you only want one.
        filename = f"{OUTPUT_PREFIX}_{i+1}.pdf"

        start_idx = i * batch_size
        end_idx = start_idx + batch_size
        batch_data = json_data[start_idx:end_idx]

        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20
        )

        elements = []

        # Logo
        try:
            logo = Image(ICON_PATH, width=60, height=60)
            logo.hAlign = 'CENTER'
            elements.append(logo)
            elements.append(Spacer(1, 10))
        except:
            pass

        # Title
        title = Paragraph("<b>examGenome CheatSheet on Algebra</b>", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 20))

        # ----------------------------------------------------
        # TABLE CONSTRUCTION (2 Columns)
        # ----------------------------------------------------
        table_data = []

        # Header Row
        table_data.append([
            Paragraph("<b>Sl.no</b>", centered_heading),
            Paragraph("<b>Content</b>", centered_heading)
        ])

        # Data Rows
        for row_index, item in enumerate(batch_data):
            sl_no = row_index + 1
            
            # Extract data from JSON
            q_text = item.get("question", "N/A")
            a_text = item.get("answer", "N/A")
            # Using .get() ensures it doesn't crash if the key is missing
            d_text = item.get("explanation", "") 

            # Combine into one string with line breaks
            # Line 1: Bold Question
            # Line 2: Answer
            # Line 3: Detailed Description
            combined_content = f"<b>{q_text}</b><br/>Answer: {a_text}<br/><font color='grey' size='9'>Explanation: {d_text}</font>"
            
            content_p = Paragraph(combined_content, content_style)
            table_data.append([str(sl_no), content_p])

        # Column Widths: Sl.no (approx 0.75 inch), Content (remaining space)
        # Total A4 width is ~595 points.
        t = Table(
            table_data,
            colWidths=[50, 480], 
            repeatRows=1
        )

        tbl_style = TableStyle([
            ('GRID', (0,0), (-1,-1), 0.4, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (0,0), (0,-1), 'CENTER'), # Center Sl.no column
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BACKGROUND', (0,0), (-1,0), colors.Color(0.85, 0.85, 0.88)),
        ])

        # Alternating row background
        for r in range(1, len(table_data)):
            bg_color = colors.white if r % 2 == 0 else colors.Color(0.97, 0.97, 0.98)
            tbl_style.add('BACKGROUND', (0, r), (-1, r), bg_color)

        t.setStyle(tbl_style)
        elements.append(t)

        # Build
        doc.build(
            elements,
            onFirstPage=draw_watermark_and_background,
            onLaterPages=draw_watermark_and_background
        )

        print(f"✔ Generated: {filename}")

if __name__ == "__main__":
    # Ensure your JSON has "question", "answer", and "detailed_description" keys
    try:
        with open(JSON_FILE, "r") as f:
            data = json.load(f)
            generate_flashcards(data)
    except FileNotFoundError:
        print(f"Error: {JSON_FILE} not found.")