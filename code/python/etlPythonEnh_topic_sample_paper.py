import os
import json
import hashlib
import random
import re
from math import ceil
from reportlab.lib.pagesizes import A4
from charset_normalizer import from_path
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
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

# === Configuration ===
INPUT_FOLDER = "trial/topicSampleJson/Percentages.json"  # Folder where your *.json files are stored
OUTPUT_PREFIX = "Percentages Topic Sample Sheet "  # Prefix for output PDF files
TOTAL_PER_PDF = 20  # Questions per PDF
LOGO_PATH = "/Users/rd/examGenome.png"
# === PAGE DIMENSIONS ===
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_OUTER = 40  # Outer white margin
INNER_MARGIN = 20  # Inner padding for content box
# === New lists as given ===
""" simpleArithmetic = [
    "Arithmetic - Percentages & Approximation",
    "Arithmetic - Percentage problem",
    "Arithmetic - Subtraction Word Problem",
    "Arithmetic - Sequence / recurrence problem",
    "Arithmetic - Unit conversion / rounding",
    "Arithmetic - Multiples and place value problem",
    "Arithmetic - Money word problem",
    "Arithmetic - Simplification / Factorisation",
    "Arithmetic - Modular / Reminder Problem",
    "Arithmetic - Speed-distance-time word problem",
    "Arithmetic - Ratio and proportion",
    "Arithmetic - Rounding and subtraction problem",
    "Arithmetic - Decimal division",
    "Arithmetic - Place value / Numbers",
    "Arithmetic - Time calculation",
    "Arithmetic - Number theory"
]

simpleNumeric = [
    "Simple numeric",
    "Arithmetic",
    "Fractions and Percentages",
    "Basic Operations",
    "Prime Numbers and Composite Numbers",
    "Product of Prime Factors",
    "HCF and LCM",
    "Arithmetic - Rounding / place value",
    "Fractions - Ratio word problem",
    "Measurement - Weight and subtraction problem"
] """
allType = []
""" EXCLUDED_TYPE = simpleArithmetic + simpleNumeric
fileMap = "encodedFile.txt" """
pool = []

#MAX_PER_TYPE = 4  # soft limit per type, still used for balanced selection

def detect_encoding(file_path):
    """Detect encoding manually via BOM + fallback to charset_normalizer."""
    with open(file_path, "rb") as f:
        raw = f.read(4)
    if raw.startswith(b'\xff\xfe\x00\x00'):
        return "utf-32le"
    elif raw.startswith(b'\x00\x00\xfe\xff'):
        return "utf-32be"
    elif raw.startswith(b'\xff\xfe'):
        return "utf-16le"
    elif raw.startswith(b'\xfe\xff'):
        return "utf-16be"
    elif raw.startswith(b'\xef\xbb\xbf'):
        return "utf-8-sig"
    # Fallback to charset_normalizer
    result = from_path(file_path).best()
    if result and result.encoding:
        return result.encoding
    return "utf-8"

def decode_unicode_escapes(obj):
    """Recursively decode unicode escape sequences in all strings."""
    if isinstance(obj, str):
        # Detect if contains any \uXXXX or \UXXXXXXXX
        if re.search(r'\\u[0-9a-fA-F]{4}|\\U[0-9a-fA-F]{8}|\\u[0-9]{4}|\\U[0-9]{4}', obj):
            try:
                return obj.encode('utf-8').decode('unicode_escape')
                #return obj.encode('utf-8').decode()
            except Exception:
                #print(f"Failed: obj")
                return obj  # return as-is if decoding fails
        return obj
    elif isinstance(obj, list):
        return [decode_unicode_escapes(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: decode_unicode_escapes(v) for k, v in obj.items()}
    else:
        return obj

def parse_json_files(folder_path):
    """Parse all *.json files from the folder and return list of dicts."""
    data_list = []
    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            encoding = detect_encoding(file_path)
            #print(f"📘 Detected encoding: {encoding}")
            with open(file_path, "r", encoding=encoding) as f:
                try:
                    content = json.load(f)
                    #print(f"Content: {content}")
                    decoded_content = decode_unicode_escapes(content)
                    if isinstance(decoded_content, dict):
                        data_list.append(decoded_content)
                    elif isinstance(decoded_content, list):
                        data_list.extend(decoded_content)
                except Exception as e:
                    print(f"⚠️ Failed to parse {filename}: {e}")

    print(f"✅ Parsed {len(data_list)} total questions.")
    return data_list
    #     try:
    #         # 🔍 Detect encoding automatically
    #         result = from_path(file_path).best()
    #         if result is None:
    #             print(f"⚠️ Could not detect encoding for {file_path}, defaulting to UTF-8.")
    #             encoding = "utf-8"
    #         else:
    #             encoding = result.encoding
    #             # Optional: confidence score for debugging
    #             print(f"Detected encoding for {file_path}: {encoding} (confidence={result.chaos:.2f})")

    #         # 📖 Open and parse using detected encoding
    #         with open(file_path, "r", encoding=encoding) as f:
    #             content = json.load(f)

    #         # ✅ Add parsed content to list
    #         if isinstance(content, dict):
    #             data_list.append(content)
    #         elif isinstance(content, list):
    #             data_list.extend(content)
    #         else:
    #             print(f"⚠️ Unexpected JSON structure in {file_path}")

    #     except Exception as e:
    #         print(f"❌ Failed to parse {file_path}: {e}")

    # return data_list
    


"""def balanced_random_selection(all_data):
    #Create a balanced randomized question list.
    type_buckets = {cls: [] for cls in CLASSIFICATIONS}

    # Distribute questions into classification buckets
    for q in all_data:
        qtype = q.get("type", "").strip()
        for cls in CLASSIFICATIONS:
            if qtype.lower().startswith(cls.lower()):
                type_buckets[cls].append(q)
                break

    # Flatten a balanced mix of questions
    selected_all = []
    all_remaining = []
    for cls, items in type_buckets.items():
        random.shuffle(items)
        selected_all.extend(items[:MAX_PER_TYPE])
        all_remaining.extend(items[MAX_PER_TYPE:])

    # Add remaining questions randomly
    random.shuffle(all_remaining)
    selected_all.extend(all_remaining)

    # Shuffle final combined list
    random.shuffle(selected_all)
    return selected_all"""

def draw_watermark(canvas, doc):
    """Draw watermark logo faintly in the background."""
    canvas.saveState()
    canvas.setFillAlpha(0.05)
    try:
        watermark = ImageReader(LOGO_PATH)
        wm_width = 900
        wm_height = 900
        canvas.drawImage(
            watermark,
            (PAGE_WIDTH - wm_width) / 2,
            (PAGE_HEIGHT - wm_height) / 2,
            width=wm_width,
            height=wm_height,
            preserveAspectRatio=True,
            mask='auto'
        )
    except Exception as e:
        print("Watermark image error:", e)
    canvas.restoreState()

def draw_bordered_frame(canvas, doc):
    """Draws a margin box around the page"""
    x0 = MARGIN_OUTER
    y0 = MARGIN_OUTER
    width = PAGE_WIDTH - 2 * MARGIN_OUTER
    height = PAGE_HEIGHT - 2 * MARGIN_OUTER

    # Outer border box
    canvas.setStrokeColor(colors.HexColor("#4B0082"))
    canvas.setLineWidth(1.2)
    canvas.rect(x0, y0, width, height, stroke=1, fill=0)

def write_to_pdf(data_list, output_pdf):
    """Write parsed JSON data to a PDF file with a formatted answer sheet."""
    '''doc = SimpleDocTemplate(output_pdf, pagesize=A4)
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    doc = SimpleDocTemplate(output_pdf, pagesize=A4,
                            leftMargin=60, rightMargin=60, topMargin=60, bottomMargin=60)'''
    doc = SimpleDocTemplate(output_pdf, 
                            pagesize=A4,
                            leftMargin=MARGIN_OUTER + INNER_MARGIN, 
                            rightMargin=MARGIN_OUTER + INNER_MARGIN, 
                            topMargin=MARGIN_OUTER + INNER_MARGIN, 
                            bottomMargin=MARGIN_OUTER + INNER_MARGIN)
    styles = getSampleStyleSheet()
    story = []

    # Custom styles
    '''title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        alignment=1,  # Center
        spaceAfter=20,
    )

    story = []'''
    # Custom styles
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
    story.append(Image(LOGO_PATH, width=360, height=460))
    story.append(Spacer(1, 20))
    #story.append(Paragraph("<b>EXAM GENIE</b>", title_style))
    #story.append(Spacer(1, 30))

    # === PRODUCT TITLE ===
    story.append(Paragraph(f"<b>Product title:</b> Mathematics MCQ for Eleven Plus - {output_pdf}", subtitle_style))
    story.append(Spacer(1, 20))

    # === CONTENT TABLE ===
    data = [
        ["Contents:", "Mathematics Sample Test"],
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
    story.append(table)
    story.append(Spacer(1, 40))

    # === FOOTER TEXT ===
    footer_text = """Thank you for your patronage.<br/>
    Visit us at <u>www.examgenome.com</u><br/>
    We regularly update our site with new products and helpful tips and advice.<br/>
    <br/>
    """
    #<b>The test should be completed in 45 minutes once you turn over the page.</b><br/>
    

    story.append(Paragraph(footer_text, subtitle_style))
    story.append(PageBreak())

    # --- Main Question Section ---
    story.append(Paragraph("Questions", title_style))
    story.append(Spacer(1, 12))

    for idx, item in enumerate(data_list, start=1):
        numbers = item.get("numbers")
        if isinstance(numbers, list) and len(numbers) > 0:
            questions = item.get("questions", [])

            # --- Question Section For statistics MCQ---
            #story.append(Paragraph(f"<b>{idx}.</b> {numbers}", normal))
            story.append(Paragraph(f"<b>{idx}.</b> {numbers}", body_style))
            story.append(Spacer(1, 10))

            # For each question inside "question" list
            for sub_idx, item in enumerate(questions, start=1):
                sub_label = f"({chr(96 + sub_idx)})"  # (i), (ii), (iii) using ascii a,b,c...

                q = item.get("question", "N/A")
                #print(f"Question: {q}")
                #if(q == 'N/A'):
                    #print(f"If clause:")
                opts = item.get("options", {})

                # Question text
                #story.append(Paragraph(f"{sub_label}: {q}", normal))
                story.append(Paragraph(f"{sub_label}: {q}", body_style))
                story.append(Spacer(1, 4))

                # Options
                for opt_key, opt_val in opts.items():
                    #story.append(Paragraph(f'{opt_key}: {opt_val}', normal))
                    story.append(Paragraph(f'{opt_key}: {opt_val}', body_style))
                story.append(Spacer(1, 10))
        else:
            q = item.get("question", "N/A")
            #print(f"Question: {q}")
            #if(q == 'N/A'):
             #   print(f"Else clause:")
            opts = item.get("options", {})

            # Question text
            #story.append(Paragraph(f"<b>{idx}.</b> {q}", normal))
            story.append(Paragraph(f"<b>{idx}.</b> {q}", content_style))
            story.append(Spacer(1, 6))

            # Options
            for opt_key, opt_val in opts.items():
                #story.append(Paragraph(f"{opt_key}: {opt_val}", normal))
                story.append(Paragraph(f"{opt_key}: {opt_val}", content_style))
            story.append(Spacer(1, 12))

    # --- Add Page Break before Answer Sheet ---
    story.append(PageBreak())

    # --- Answer Sheet Section ---
    story.append(Paragraph("Answer Sheet", title_style))
    story.append(Spacer(1, 12))

    # Create formatted table of answers
    answers = []
    for idx, item in enumerate(data_list, start=1):
        numbers = item.get("numbers")
        if isinstance(numbers, list) and len(numbers) > 0:
            for sub_idx, item in enumerate(questions, start=1):
                sub_label = f"{idx}({chr(96 + sub_idx)})"
                ans = item.get("answer", "N/A")
                answers.append(f"{sub_label}: {ans}")
        else:
            ans = item.get("answer", "N/A")
            answers.append(f"{idx}. {ans}")

    # Format answers into rows of 5 columns
    num_cols = 5
    table_data = [answers[i : i + num_cols] for i in range(0, len(answers), num_cols)]

    answer_table = Table(table_data, colWidths=[90] * num_cols)
    answer_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.grey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(answer_table)
    story.append(Spacer(1, 12))

    doc.build(story, onFirstPage=draw_bordered_frame, onLaterPages=draw_watermark)
    print(f"✅ Created PDF: {output_pdf} ({len(data_list)} questions)")


# === New lists as given ===
simpleArithmetic = [
    "Arithmetic - Percentages & Approximation",
    "Arithmetic - Percentage problem",
    "Arithmetic - Subtraction Word Problem",
    "Arithmetic - Sequence / recurrence problem",
    "Arithmetic - Unit conversion / rounding",
    "Arithmetic - Multiples and place value problem",
    "Arithmetic - Money word problem",
    "Arithmetic - Simplification / Factorisation",
    "Arithmetic - Modular / Reminder Problem",
    "Arithmetic - Speed-distance-time word problem",
    "Arithmetic - Ratio and proportion",
    "Arithmetic - Rounding and subtraction problem",
    "Arithmetic - Decimal division",
    "Arithmetic - Place value / Numbers",
    "Arithmetic - Time calculation",
    "Arithmetic - Number theory",
    "Arithmetic - Number Theory / LCM",
    "Arithmetic - Sequences & Patterns"
]

simpleNumeric = [
    "Simple numeric",
    "Arithmetic",
    "Fractions and Percentages",
    "Basic Operations",
    "Prime Numbers and Composite Numbers",
    "Product of Prime Factors",
    "HCF and LCM",
    "Arithmetic - Rounding / place value",
    "Fractions - Ratio word problem",
    "Measurement - Weight and subtraction problem"
]


"""def select_questions(all_data, used, key, values, count, key_type="type"):
    #Select random questions based on key-value match (type/difficulty).
    pool = [q for q in all_data if q.get(key_type) in values and id(q) not in used]
    random.shuffle(pool)
    selected = pool[:count]
    for q in selected:
        used.add(id(q))
    return selected"""


def question_signature(q):
    """Generate a stable unique ID for a question based on its content."""
    try:
        # Use deterministic JSON dump as base for hashing
        #print("Q :"+str(q))
        q_str = json.dumps(q, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(q_str.encode("utf-8")).hexdigest()
    except Exception:
        # Fallback to id() if hashing fails (rare)
        return str(id(q))

"""def select_questions(all_data, used, key, values, count, key_type="type"):
    #Select random questions based on key-value match (type/difficulty),
       ensuring no duplicate questions across PDFs.
    #
    # Filter questions by type/difficulty and exclude already-used signatures
    pool = []
    for q in all_data:    
        if q.get(key_type) in values:
            sig = question_signature(q)
            if sig not in used:
                pool.append((sig, q))

    random.shuffle(pool)
    selected = [q for _, q in pool[:count]]

    # Mark these selected questions as used
    for sig, _ in pool[:count]:
        used.add(sig)

    return selected"""

#def select_questions(all_data, used, qBlock, filters, count):
def select_questions(all_data, used, count):
    """
    Select random questions based on multiple filters (e.g. type and/or difficulty),
    ensuring no duplicate questions across PDFs.
    Example filters: {"type": ["Fractions", "Arithmetic"], "difficulty": ["easy"]}
    """
    selected = []
    #if len(pool) == 0:
    
    for q in all_data:
        """ # Check all filter conditions
        for k, v in filters.items():
            print("K : "+str(k))
            print("V : "+str(v))
        
        if all(q.get(k) in v for k, v in filters.items()):
            sig = question_signature(q)
            #print("FNUMBER : "+str(q.get('fnumber'))) """
            
        sig = question_signature(q.get('question'))    
        if sig not in used:
            pool.append((sig, q))
            #print("Q : "+str(q))
            

    #random.shuffle(pool)
    #print("Pool :"+str(pool))
    
    #print("Sel : "+str(selected))
    selected = [(s,q) for s, q in pool if s not in used]
    temp_list = [(s, q) for s, q in selected[:count]]
    

    # 2. Unpack the list of tuples into two separate lists using zip
    signatures, questions = zip(*temp_list)

    # Note: The result of zip is a tuple of lists/tuples, so you might want to convert them if needed
    signatures = list(signatures)
    """ for t in questions:
        #print("T :"+str(t.get("fnumber")))
        qBlock.append(t.get("fnumber")) """
    questions = list(questions)
    #print("CASESELECTED: "+str(caseSelected))
    #print("Selected :"+str(caseSelected))
    """ print("Length:"+str(len(questions)))
    print("QBLOCK: "+str(qBlock)) """
    # Mark these selected questions as used
    """for sig, _ in pool[:count]:
        used.add(sig)
    print("USED : "+str(used))
    random.shuffle(selected)
    return selected"""

    for sig in signatures:
        used.add(sig)
    #print("USED : "+str(used))
    """ with open(fileMap, 'a') as file:
        file.write(str(used)) """
    random.shuffle(questions)
    return questions




def create_multiple_pdfs(all_data):
    """Create multiple PDFs of 50 questions each with structured composition."""
    total_questions = len(all_data)
    print("All_Data: "+str(all_data))
    if total_questions == 0:
        print("❌ No data to process.")
        return

    num_pdfs = ceil(total_questions / TOTAL_PER_PDF)
    print(f"📦 Found {total_questions} total questions → will create {num_pdfs} PDFs")

    used_questions = set()
    
    pdf_counter = 0

    """ strategy = {
                'sN': [{"difficulty": "easy"}, {"difficulty": "medium"}, {"difficulty": "hard"},{"difficulty": ['easy','medium','hard']}],
                'sA': [{"difficulty": "easy"}, {"difficulty": "medium"}, {"difficulty": "hard"},{"difficulty": ['medium','easy','hard']}],
                'm': [{"difficulty": "medium"}, {"difficulty": "hard"}, {"difficulty": "easy"},{"difficulty": ['easy','medium']}],
                'h': [{"difficulty": "hard"}, {"difficulty": "easy"}, {"difficulty": "easy"},{"difficulty": ['medium','hard']}]
    } """

    for i in range(4):
        #questionBlock = []
        print(f"\n🧮 Preparing PDF {i + 1}...")

        # --- 4️⃣ Last 15 questions: hard difficulty only ---
        section4 = select_questions(
            all_data,
            used_questions,
            #{"difficulty": ["hard"]},
            #questionBlock,
            #{"difficulty": strategy["h"][i]["difficulty"], "type":[t for t in allType if t not in EXCLUDED_TYPE], "fnumber": [f for f in allFnumber if f not in questionBlock]},
            #{"difficulty": ["hard"], "type":[t for t in allType if t not in EXCLUDED_TYPE]},
            20
        )


        # Combine all parts for the PDF
        batch = section4
        #random.shuffle(batch)  # Shuffle slightly for randomness in final layout

        if len(batch) < 20:
            print(f"⚠️ Only {len(batch)} questions assembled — skipping incomplete PDF.")
            break

        pdf_counter += 1
        """if not batch:
            print(f"⚠️ Skipping empty batch for PDF {i + 1}")
            continue"""

        output_pdf = f"{OUTPUT_PREFIX}{i + 1}.pdf"
        decoded_content = decode_unicode_escapes(batch)
        write_to_pdf(decoded_content, output_pdf)
        print(f"✅ Created {output_pdf} ({len(batch)} questions)")



if __name__ == "__main__":
    all_data = {}
    try:
        with open(INPUT_FOLDER, 'r') as file:
            all_data = json.load(file)
        # The Python lambda function
        #get_type = lambda item: item.get('type')
    
    except FileNotFoundError:
        print("Error: The file {INPUT_FOLDER} was not found.")
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from the file. Check for malformed JSON.")

    """ # Example usage with map (or a list comprehension)
    allType = list(map(get_type, all_data))

    # The Python lambda function
    get_fnumber = lambda item: item.get('fnumber')

    # Example usage with map (or a list comprehension)
    allFnumber = list(map(get_fnumber, all_data)) """
    
    if not all_data:
        print("❌ No valid JSON files found.")
    else:
        create_multiple_pdfs(all_data)
