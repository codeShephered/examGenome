import os
import json
import hashlib
import random
import re
from math import ceil
from collections import Counter

from reportlab.lib.pagesizes import A4
from charset_normalizer import from_path
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak,
    Table,
    TableStyle,
)

# ============================================================
# === Configuration ===
# ============================================================
INPUT_FILE = "../../jsons/year456/src/extracted_y3Number_placevalue.json"
OUTPUT_PREFIX = "Year3 - Number Place and value"
content_output = f"{OUTPUT_PREFIX}"
TOTAL_PER_PDF = 30          # Questions per PDF
QUESTIONS_PER_DIFFICULTY = TOTAL_PER_PDF // 3   # 10 easy + 10 medium + 10 hard = 30
LOGO_PATH = "/Users/rd/examGenome.png"

# If the last leftover batch has fewer than TOTAL_PER_PDF questions (e.g. 308
# total / 30 per PDF leaves 8 over), still produce a shorter final PDF for
# them instead of discarding those questions. Set to False to only ever
# produce full-length PDFs.
ALLOW_PARTIAL_LAST_PDF = True

# === PAGE DIMENSIONS ===
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_OUTER = 40
INNER_MARGIN = 20

# Kept for reference / future use if you want to filter by "type" as well as
# "difficulty" — not currently applied as a filter since it isn't guaranteed
# every question object has a "type" field that matches these exactly.
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
    "Arithmetic - Sequences & Patterns",
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
    "Measurement - Weight and subtraction problem",
]


# ============================================================
# === JSON parsing helpers ===
# ============================================================
def detect_encoding(file_path):
    """Detect encoding manually via BOM + fallback to charset_normalizer."""
    with open(file_path, "rb") as f:
        raw = f.read(4)
    if raw.startswith(b"\xff\xfe\x00\x00"):
        return "utf-32le"
    elif raw.startswith(b"\x00\x00\xfe\xff"):
        return "utf-32be"
    elif raw.startswith(b"\xff\xfe"):
        return "utf-16le"
    elif raw.startswith(b"\xfe\xff"):
        return "utf-16be"
    elif raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    result = from_path(file_path).best()
    if result and result.encoding:
        return result.encoding
    return "utf-8"


def decode_unicode_escapes(obj):
    """Recursively decode unicode escape sequences in all strings."""
    if isinstance(obj, str):
        if re.search(r"\\u[0-9a-fA-F]{4}|\\U[0-9a-fA-F]{8}", obj):
            try:
                return obj.encode("utf-8").decode("unicode_escape")
            except Exception:
                return obj
        return obj
    elif isinstance(obj, list):
        return [decode_unicode_escapes(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: decode_unicode_escapes(v) for k, v in obj.items()}
    else:
        return obj


def parse_json_files(file_path):
    """
    Parse a JSON file and return a flat list of question dicts.
    Handles:
      - top-level list:            [ {...}, {...} ]
      - top-level dict wrapper:    { "questions": [ {...}, ... ] }
      - top-level single dict:     { ...single question... }
    """
    data_list = []

    encoding = detect_encoding(file_path)
    with open(file_path, "r", encoding=encoding) as f:
        try:
            content = json.load(f)
            decoded_content = decode_unicode_escapes(content)

            if isinstance(decoded_content, list):
                data_list.extend(decoded_content)
            elif isinstance(decoded_content, dict):
                # Try common wrapper keys first
                for key in ("questions", "data", "items"):
                    if key in decoded_content and isinstance(decoded_content[key], list):
                        data_list.extend(decoded_content[key])
                        break
                else:
                    # No known wrapper key found — treat as a single record
                    data_list.append(decoded_content)
        except Exception as e:
            print(f"⚠️ Failed to parse {file_path}: {e}")

    print(f"✅ Parsed {len(data_list)} total questions.")
    return data_list


def get_options(item):
    """
    Return a flat {A: ..., B: ...} options dict, unwrapping any accidental
    double-nesting such as {"options": {"options": {...}}}.
    """
    opts = item.get("options", {}) or {}
    while isinstance(opts, dict) and "options" in opts and isinstance(opts["options"], dict):
        opts = opts["options"]
    return opts


def question_signature(q):
    """Generate a stable unique ID for a question based on its content."""
    try:
        q_str = json.dumps(q, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(q_str.encode("utf-8")).hexdigest()
    except Exception:
        return str(id(q))


def is_in(value, allowed):
    """True if `value` matches `allowed`, whether allowed is scalar or a collection."""
    if isinstance(allowed, (list, tuple, set)):
        return value in allowed
    return value == allowed


# ============================================================
# === Question selection ===
# ============================================================
def select_questions(all_data, used, filters, count):
    """
    Select up to `count` random questions matching ALL key/value pairs in
    `filters` (e.g. {"difficulty": "easy"} or {"difficulty": ["easy","medium"]}),
    skipping any question already present in `used` (a set of signatures).

    Never raises on an empty match — returns [] and prints a warning instead.
    """
    pool = []
    for q in all_data:
        if all(is_in(q.get(k), v) for k, v in filters.items()):
            sig = question_signature(q)
            if sig not in used:
                pool.append((sig, q))

    random.shuffle(pool)
    chosen = pool[:count]

    if len(chosen) < count:
        print(f"⚠️ Only found {len(chosen)}/{count} unused questions matching {filters}")

    if not chosen:
        return []

    for sig, _ in chosen:
        used.add(sig)

    return [q for _, q in chosen]


# ============================================================
# === PDF drawing helpers ===
# ============================================================
def draw_watermark(canvas_obj, doc):
    """Draw watermark logo faintly in the background."""
    canvas_obj.saveState()
    canvas_obj.setFillAlpha(0.05)
    try:
        watermark = ImageReader(LOGO_PATH)
        wm_width = 900
        wm_height = 900
        canvas_obj.drawImage(
            watermark,
            (PAGE_WIDTH - wm_width) / 2,
            (PAGE_HEIGHT - wm_height) / 2,
            width=wm_width,
            height=wm_height,
            preserveAspectRatio=True,
            mask="auto",
        )
    except Exception as e:
        print("Watermark image error:", e)
    canvas_obj.restoreState()


def draw_bordered_frame(canvas_obj, doc):
    """Draws a margin box around the page."""
    x0 = MARGIN_OUTER
    y0 = MARGIN_OUTER
    width = PAGE_WIDTH - 2 * MARGIN_OUTER
    height = PAGE_HEIGHT - 2 * MARGIN_OUTER

    canvas_obj.setStrokeColor(colors.HexColor("#4B0082"))
    canvas_obj.setLineWidth(1.2)
    canvas_obj.rect(x0, y0, width, height, stroke=1, fill=0)


# ============================================================
# === PDF writing ===
# ============================================================
def write_to_pdf(data_list, output_pdf):
    """Write parsed question data to a PDF file with a formatted answer sheet."""
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        leftMargin=MARGIN_OUTER + INNER_MARGIN,
        rightMargin=MARGIN_OUTER + INNER_MARGIN,
        topMargin=MARGIN_OUTER + INNER_MARGIN,
        bottomMargin=MARGIN_OUTER + INNER_MARGIN,
    )
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        alignment=1,
        fontSize=20,
        textColor=colors.HexColor("#4B0082"),
        spaceAfter=10,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"], fontSize=12, spaceAfter=20, alignment=1
    )
    content_style = ParagraphStyle(
        "Content", parent=styles["Normal"], fontSize=11, spaceAfter=12
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"], fontSize=11, spaceAfter=10
    )

    # === LOGO & TITLE ===
    story.append(Image(LOGO_PATH, width=360, height=460))
    story.append(Spacer(1, 20))
    story.append(
        Paragraph(f"<b>Product title:</b> Mathematics MCQ for Eleven Plus - {output_pdf}", subtitle_style)
    )
    story.append(Spacer(1, 20))

    # === CONTENT TABLE ===
    data = [
        ["Contents:", f"{content_output}"],
        ["Answer Sheet", "1 page"],
    ]
    table = Table(data, colWidths=[250, 100])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("ALIGN", (1, 1), (1, -1), "LEFT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TEXTCOLOR", (0, 0), (0, 0), colors.black),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 40))

    # === FOOTER TEXT ===
    footer_text = """Thank you for your patronage.<br/>
    Visit us at <u>www.examgenome.com</u><br/>
    We regularly update our site with new products and helpful tips and advice.<br/>
    <br/>
    <br/>
    """
    story.append(Paragraph(footer_text, subtitle_style))
    story.append(PageBreak())

    # --- Main Question Section ---
    story.append(Paragraph("Questions", title_style))
    story.append(Spacer(1, 12))

    for idx, entry in enumerate(data_list, start=1):
        numbers = entry.get("numbers")

        if isinstance(numbers, list) and len(numbers) > 0:
            # --- Grouped question (e.g. a shared "numbers" context with sub-parts) ---
            sub_questions = entry.get("questions", [])

            story.append(Paragraph(f"<b>{idx}.</b> {numbers}", body_style))
            story.append(Spacer(1, 10))

            for sub_idx, sub_item in enumerate(sub_questions, start=1):
                sub_label = f"({chr(96 + sub_idx)})"  # (a), (b), (c)...
                q = sub_item.get("question", "N/A")
                opts = get_options(sub_item)

                story.append(Paragraph(f"{sub_label}: {q}", body_style))
                story.append(Spacer(1, 4))
                for opt_key, opt_val in opts.items():
                    story.append(Paragraph(f"{opt_key}: {opt_val}", body_style))
                story.append(Spacer(1, 10))
        else:
            # --- Single standalone question ---
            q = entry.get("question", "N/A")
            opts = get_options(entry)

            story.append(Paragraph(f"<b>{idx}.</b> {q}", content_style))
            story.append(Spacer(1, 6))
            for opt_key, opt_val in opts.items():
                story.append(Paragraph(f"{opt_key}: {opt_val}", content_style))
            story.append(Spacer(1, 12))

    story.append(PageBreak())

    # --- Answer Sheet Section ---
    story.append(Paragraph("Answer Sheet", title_style))
    story.append(Spacer(1, 12))

    answers = []
    for idx, entry in enumerate(data_list, start=1):
        numbers = entry.get("numbers")

        if isinstance(numbers, list) and len(numbers) > 0:
            sub_questions = entry.get("questions", [])
            for sub_idx, sub_item in enumerate(sub_questions, start=1):
                sub_label = f"{idx}({chr(96 + sub_idx)})"
                ans = sub_item.get("answer", "N/A")
                answers.append(f"{sub_label}: {ans}")
        else:
            ans = entry.get("answer", "N/A")
            answers.append(f"{idx}. {ans}")

    num_cols = 5
    table_data = [answers[i:i + num_cols] for i in range(0, len(answers), num_cols)]
    if table_data and len(table_data[-1]) < num_cols:
        table_data[-1] += [""] * (num_cols - len(table_data[-1]))

    if table_data:
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


# ============================================================
# === PDF batching / orchestration ===
# ============================================================
def create_multiple_pdfs(all_data):
    """Create multiple PDFs of TOTAL_PER_PDF questions each, balanced by difficulty."""
    total_questions = len(all_data)
    if total_questions == 0:
        print("❌ No data to process.")
        return

    num_pdfs = ceil(total_questions / TOTAL_PER_PDF)
    print(f"📦 Found {total_questions} total questions → will attempt up to {num_pdfs} PDFs")

    used_questions = set()

    # Not every dataset tags questions with a "difficulty" field. If none of
    # the questions have one, filtering by difficulty would always return
    # zero results — so fall back to plain random selection instead.
    has_difficulty = any(q.get("difficulty") for q in all_data)
    if not has_difficulty:
        print(
            "ℹ️ No 'difficulty' field found on any question — "
            "selecting questions purely at random instead of by difficulty."
        )

    for i in range(num_pdfs):
        print(f"\n🧮 Preparing PDF {i + 1}...")

        if has_difficulty:
            section1 = select_questions(
                all_data, used_questions, {"difficulty": "easy"}, QUESTIONS_PER_DIFFICULTY
            )
            section2 = select_questions(
                all_data, used_questions, {"difficulty": "medium"}, QUESTIONS_PER_DIFFICULTY
            )
            section3 = select_questions(
                all_data, used_questions, {"difficulty": "hard"}, QUESTIONS_PER_DIFFICULTY
            )
            batch = section1 + section2 + section3
        else:
            batch = select_questions(all_data, used_questions, {}, TOTAL_PER_PDF)

        random.shuffle(batch)

        if len(batch) == 0:
            print("⚠️ No questions left to assemble — stopping.")
            break

        if len(batch) < TOTAL_PER_PDF:
            if not ALLOW_PARTIAL_LAST_PDF:
                print(
                    f"⚠️ Only {len(batch)} questions assembled (needed {TOTAL_PER_PDF}) "
                    f"— stopping, no more full PDFs can be built."
                )
                break
            print(f"ℹ️ Only {len(batch)} questions left — creating a shorter final PDF.")

        output_pdf = f"{OUTPUT_PREFIX}{i + 1}.pdf"
        #output_pdf = f"{OUTPUT_PREFIX}_sample.pdf" if i == 0 else f"{OUTPUT_PREFIX}{i}.pdf"
        write_to_pdf(batch, output_pdf)
        print(f"✅ Created {output_pdf} ({len(batch)} questions)")


# ============================================================
# === Entry point ===
# ============================================================
if __name__ == "__main__":
    all_data = parse_json_files(INPUT_FILE)

    if not all_data:
        print("❌ No valid JSON data found.")
    else:
        # Diagnostics — helps confirm the data actually has a "difficulty" field
        # before we try to filter on it.
        sample_keys = set(all_data[0].keys())
        print(f"🔍 Sample question keys: {sample_keys}")

        diff_counts = Counter(q.get("difficulty", "MISSING") for q in all_data)
        print(f"🔍 Difficulty distribution: {dict(diff_counts)}")

        create_multiple_pdfs(all_data)
