import json
import math
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.pdfencrypt import StandardEncryption
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak,
    Table,
    TableStyle,
    Frame,
)

# --- Configuration ---
JSON_FILE = 'longDivFlashCard.json' # Your input file
ICON_PATH = 'examGenomeTrp.png'       # Your watermark icon (Ensure this file exists!)
OUTPUT_PREFIX = 'examGenome_flashCard_longDivision'
MARGIN_OUTER = 40  # Outer white margin
INNER_MARGIN = 20  # Inner padding for content box

# --- 10 Distinct Pastel Colors for backgrounds ---
CARD_COLORS = [
    colors.Color(0.9, 0.9, 1),      # Light Blue
    colors.Color(0.9, 1, 0.9),      # Light Green
    colors.Color(1, 0.9, 0.9),      # Light Red
    colors.Color(1, 1, 0.8),        # Light Yellow
    colors.Color(0.9, 1, 1),        # Light Cyan
    colors.Color(1, 0.9, 1),        # Light Magenta
    colors.Color(0.95, 0.95, 0.95), # Light Grey
    colors.Color(1, 0.85, 0.8),     # Light Orange
    colors.Color(0.8, 0.9, 1),      # Periwinkle
    colors.Color(0.85, 1, 0.85)     # Mint
]

class FlashcardBox(Flowable):
    """
    Custom Flowable to draw a flashcard with:
    1. Specific Background Color
    2. Internal Watermark
    3. Dotted Border (for tearing)
    4. Text Content
    """
    def __init__(self, index, question_text, bg_color, width, height):
        Flowable.__init__(self)
        self.index = index
        self.question_text = question_text
        self.bg_color = bg_color
        self.width = width
        self.height = height
        self.styles = getSampleStyleSheet()
        
        # Create the Paragraph for the text
        p_style = ParagraphStyle(
            'QStyle', 
            parent=self.styles['Normal'], 
            fontSize=11, 
            leading=14,
            alignment=1 # Center alignment
        )
        # Combine Index and Question
        full_text = f"<b>Q{index}:</b><br/><br/>{question_text}"
        self.paragraph = Paragraph(full_text, p_style)

    def draw(self):
        canvas = self.canv
        x, y = 0, 0 # Draw relative to the flowable's frame
        
        canvas.saveState()
        
        # 1. Draw Background
        canvas.setFillColor(self.bg_color)
        canvas.rect(x, y, self.width, self.height, fill=1, stroke=0)
        
        # 2. Draw Watermark (Centered in this specific box)
        if os.path.exists(ICON_PATH):
            try:
                # Set transparency
                canvas.setFillAlpha(0.3)
                # Calculate center
                img_w, img_h = 100, 100 
                center_x = self.width / 2 - (img_w / 2)
                center_y = self.height / 2 - (img_h / 2)
                canvas.drawImage(ICON_PATH, center_x, center_y, width=img_w, height=img_h, mask='auto', preserveAspectRatio=True, anchor='c')
                # Reset Alpha
                canvas.setFillAlpha(1)
            except:
                pass

        # 3. Draw Text
        # We need to wrap the paragraph to fit the box width minus padding
        padding = 10
        avail_w = self.width - (padding * 2)
        avail_h = self.height - (padding * 2)
        
        w, h = self.paragraph.wrap(avail_w, avail_h)
        # Center text vertically
        text_y = (self.height - h) / 2
        self.paragraph.drawOn(canvas, padding, text_y)

        # 4. Draw Dotted Border (The "Tear" line)
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(1)
        canvas.setDash(3, 3) # 3 points on, 3 points off
        canvas.rect(x, y, self.width, self.height, fill=0, stroke=1)

        canvas.restoreState()

def draw_background_watermark(canvas, doc):
    """
    This function draws watermarks on the Answer/Details pages (Page 2+).
    """
    # Only draw this if we are NOT on page 1 (since page 1 has box-specific watermarks)
    if doc.page > 1:
        canvas.saveState()
        try:
            if os.path.exists(ICON_PATH):
                canvas.setFillAlpha(0.05)
                # Draw a large watermark in the center of the page
                page_w, page_h = A4
                #canvas.drawImage(ICON_PATH, page_w/2 - 50, page_h/2 - 50, width=100, height=100, mask='auto', preserveAspectRatio=True, anchor='c')
                watermark = ImageReader(ICON_PATH)
                wm_width = 900
                wm_height = 900
                canvas.drawImage(
                watermark,
                (page_w - wm_width) / 2,
                (page_h - wm_height) / 2,
                width=wm_width,
                height=wm_height,
                preserveAspectRatio=True,
                mask='auto'
                )
        except:
            pass
        canvas.restoreState()

def generate_flashcards(json_data):
    # Security: No Copy, No Print
    #enc = StandardEncryption("", "owner", canPrint=0)

    batch_size = 10
    total_batches = math.ceil(len(json_data) / batch_size)

    for i in range(total_batches):
        batch_num = i + 1
        filename = f"{OUTPUT_PREFIX}-{batch_num}.pdf"
        
        start_idx = i * batch_size
        end_idx = start_idx + batch_size
        batch_data = json_data[start_idx:end_idx]

        doc = SimpleDocTemplate(
            filename, 
            pagesize=A4,
            rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20
            #encrypt=enc
        )

        elements = []
        styles = getSampleStyleSheet()
        # --- STARTING PAGE ---
        title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        alignment=1,
        fontSize=20,
        textColor=colors.HexColor("#4B0082"),
        spaceAfter=10,
        )

        subtitle_style = ParagraphStyle(
            "Subtitle",
            parent=styles["Normal"],
            fontSize=12,
            spaceAfter=20,
            alignment=1
        )

        content_style = ParagraphStyle(
            "Content",
            parent=styles["Normal"],
            fontSize=11,
            spaceAfter=12,
        )

        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=11,
            spaceAfter=10,
        )

        # === LOGO & TITLE ===
        elements.append(Image(ICON_PATH, width=360, height=460))
        elements.append(Spacer(1, 20))
        #story.append(Paragraph("<b>EXAM GENIE</b>", title_style))
        #story.append(Spacer(1, 30))

        # === PRODUCT TITLE ===
        elements.append(Paragraph(f"<b>Product title:</b> Mathematics MCQ for Eleven Plus - {filename}", subtitle_style))
        elements.append(Spacer(1, 20))

        # === CONTENT TABLE ===
        data = [
            ["Contents:", "Mathematics"],
            ["Answer Sheet", "1 page"],
            
        ]

        table = Table(data, colWidths=[250, 100])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 40))

        # === FOOTER TEXT ===
        footer_text = """Thank you for your patronage.<br/>
        Visit us at <u>www.examgenome.com</u><br/>
        We regularly update our site with new products and helpful tips and advice.<br/>
        <br/>
        """

        elements.append(Paragraph(footer_text, subtitle_style))
        elements.append(PageBreak())

        # --- PAGE 1: FLASHCARDS ---
        
        title = Paragraph("<b>examGenome Flashcard on Long Division</b>", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 15))

        # Calculate Box Size
        # A4 Width ~595pts. Margins 40. Avail Width ~555.
        # We want 2 columns. Box Width ~270.
        # A4 Height ~842. Title ~50. Avail Height ~750.
        # We want 5 rows (10 items total). Box Height ~140.
        
        box_w = 265
        box_h = 135
        
        flashcard_objs = []
        
        # Create FlashcardBox objects
        for idx, item in enumerate(batch_data):
            # Requirements: Numeral starts from 1 to 10 per PDF
            local_index = idx + 1 
            
            # Requirement: Different background color for each
            bg_color = CARD_COLORS[idx % len(CARD_COLORS)]
            
            box = FlashcardBox(
                local_index, 
                item.get('question', ''), 
                bg_color, 
                box_w, 
                box_h
            )
            flashcard_objs.append(box)

        # Arrange boxes in a 2-column Table for layout
        # Convert list of 10 items into list of lists [[1,2], [3,4]...]
        grid_data = []
        for j in range(0, len(flashcard_objs), 2):
            row = flashcard_objs[j:j+2]
            # Handle if last row has only 1 item
            if len(row) < 2:
                row.append('') 
            grid_data.append(row)

        t = Table(grid_data, colWidths=[box_w + 10, box_w + 10], rowHeights=[box_h + 10]*len(grid_data))
        
        # Center the table contents
        t.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        
        elements.append(t)
        elements.append(PageBreak())

        # --- PAGE 2: ANSWERS ---
        
        title_ans = Paragraph("<b>Answers and Details</b>", styles['Title'])
        elements.append(title_ans)
        elements.append(Spacer(1, 20))

        for idx, item in enumerate(batch_data):
            local_index = idx + 1
            
            # Subtitle
            elements.append(Paragraph(f"<b>Question {local_index}</b>", styles['Heading3']))
            
            # Answer Content
            ans_style = styles['Normal']
            elements.append(Paragraph(f"<b>Answer:</b> {item.get('answer')}", ans_style))
            elements.append(Spacer(1, 5))
            elements.append(Paragraph(f"<i>Details:</i> {item.get('details')}", ans_style))
            
            elements.append(Spacer(1, 15))
            elements.append(Paragraph("_" * 60, styles['Normal']))
            elements.append(Spacer(1, 15))

        # Build with watermark on later pages
        try:
            doc.build(elements, onLaterPages=draw_background_watermark)
            print(f"Successfully generated: {filename}")
        except Exception as e:
            print(f"Error: {e}")

# --- Test Data Generation ---
if __name__ == "__main__":
    # Create Dummy JSON
    # dummy_data = []
    # for k in range(1, 26): 
    #     dummy_data.append({
    #         "question": f"Calculate {k*543} / 3. Show remainder.",
    #         "answer": f"{k*181}",
    #         "details": "Step 1: Setup dividend and divisor. Step 2: Calculate first digit..."
    #     })
    
    # Write JSON
    # with open(JSON_FILE, 'w') as f:
    #     json.dump(dummy_data, f)
        
    # Check for icon
    if not os.path.exists(ICON_PATH):
        print(f"WARNING: '{ICON_PATH}' not found. Watermarks will be skipped.")
        # Create a dummy blank file to prevent crash if user forgets
        # form reportlab.lib.utils import ImageReader
        # In real scenario, user must provide the image.

    # Run
    with open(JSON_FILE, 'r') as f:
        data = json.load(f)
        generate_flashcards(data)