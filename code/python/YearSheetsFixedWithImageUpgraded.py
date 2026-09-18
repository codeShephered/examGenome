import os
import json
import hashlib
import random
import re
import base64
import io
import time
import textwrap
import traceback
import anthropic
from math import ceil
from collections import Counter
from pypdf import PdfWriter, PdfReader

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
    KeepTogether,
)

# ============================================================
# === Configuration ===
# ============================================================
INPUT_FILE = "../../jsons/year456/src/y3Geometry_properties_of_shapes.json"
OUTPUT_PREFIX = "Year3-Geometry_Properties_of_shapes"
content_output = f"{OUTPUT_PREFIX}"
TOTAL_PER_PDF = 30
QUESTIONS_PER_DIFFICULTY = TOTAL_PER_PDF // 3   # 10 easy + 10 medium + 10 hard
LOGO_PATH = "/Users/rd/examGenome.png"
ALLOW_PARTIAL_LAST_PDF = True

# ── Claude image generation settings ──────────────────────────────────────────
# Claude generates matplotlib Python code for each visual question.
# That code is executed locally to produce a PNG which is embedded in the PDF.
# Set ENABLE_IMAGE_GENERATION = False to skip all image generation.
ENABLE_IMAGE_GENERATION = True

# Image cache directory — generated PNGs are cached so re-runs don't re-call API.
IMAGE_CACHE_DIR = ".question_images"

# Embedded image size in PDF (points; 1 pt ≈ 0.35 mm).
IMAGE_PDF_WIDTH  = 160
IMAGE_PDF_HEIGHT = 140

# Seconds between successive Claude API calls — avoids rate-limiting.
API_CALL_DELAY = 0.5

# ── Anthropic workspace ID ─────────────────────────────────────────────────────
# Required when using an org-level API key (not scoped to a specific workspace).
# Find it in console.anthropic.com → Settings → Workspaces → click your workspace
# → copy the "Workspace ID" (starts with "wrkspc_...").
# Leave empty ("") if your key is already workspace-scoped — it will be ignored.
ANTHROPIC_WORKSPACE_ID = os.environ.get("ANTHROPIC_WORKSPACE_ID", "")

# ── Claude client ──────────────────────────────────────────────────────────────
def _make_claude_client() -> anthropic.Anthropic:
    """
    Build the Anthropic client, injecting the workspace ID header when the key
    is org-level (not scoped to a workspace).  The header is ignored by the SDK
    if it is an empty string.
    """
    kwargs: dict = {}
    ws_id = ANTHROPIC_WORKSPACE_ID.strip()
    if ws_id:
        kwargs["default_headers"] = {"anthropic-workspace-id": ws_id}
    return anthropic.Anthropic(**kwargs)

_claude = _make_claude_client()

# === PAGE DIMENSIONS ===
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_OUTER = 40
INNER_MARGIN = 20

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
# === Image generation helpers ===
# ============================================================

# Keywords that suggest the question benefits from a diagram.
_VISUAL_KEYWORDS = (
    "coordinate", "coordinates", "grid", "plot", "point", "vertex", "vertices",
    "triangle", "rectangle", "pentagon", "hexagon", "polygon", "shape", "quadrant",
    "translate", "translation", "reflect", "reflection", "rotate", "rotation",
    "length", "perimeter", "area", "distance", "diagonal", "side", "angle",
    "x-axis", "y-axis", "origin", "graph", "ruler", "measure", "compass",
    "scale", "diagram", "draw", "sketch", "figure", "number line",
)


def _needs_image(question_text: str, options: dict) -> bool:
    """Return True when the question is likely to benefit from a visual diagram."""
    combined = question_text.lower() + " ".join(str(v) for v in options.values()).lower()
    return any(kw in combined for kw in _VISUAL_KEYWORDS)


def _cache_path(question_text: str) -> str:
    """Return a stable file path for caching this question's image."""
    digest = hashlib.md5(question_text.encode("utf-8")).hexdigest()
    os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)
    return os.path.join(IMAGE_CACHE_DIR, f"{digest}.png")


def _build_code_prompt(question_text: str, options: dict) -> str:
    """
    Ask Claude to write matplotlib code that draws a diagram for the question.
    We ask for self-contained code that saves the figure to OUTPUT_PATH.
    Answers and answer labels are explicitly excluded from the diagram.
    """
    # Pass option labels only (not values) so Claude cannot draw the answer
    option_labels = list(options.keys())   # ["A", "B", "C", "D"]
    return textwrap.dedent(f"""
        You are a Python code generator for primary-school maths diagrams.

        Write a complete, self-contained Python script using matplotlib that draws
        a clear, minimal diagram illustrating the QUESTION CONTEXT below.

        STRICT RULES — violating any rule means the image will be rejected:
        1. Use ONLY matplotlib and the Python standard library (no other imports).
        2. White background, clean axes, large readable labels/tick marks.
        3. Figure size: 4 × 3 inches at 100 dpi (400×300 px).
        4. Save with: plt.savefig(OUTPUT_PATH, dpi=100, bbox_inches='tight')
        5. Do NOT call plt.show().
        6. OUTPUT_PATH is pre-defined — do not re-define it.
        7. NEVER include the question text in the diagram.
        8. NEVER label, mark, highlight or indicate ANY of the answer options
           ({", ".join(option_labels)}). The diagram must show ONLY the geometric
           or visual context — no correct answer, no hints, no answer labels.
        9. Draw only: grids, axes, unlabelled shapes, points, number lines,
           measurement scales — nothing that reveals the answer.

        Question context (use this to decide what to draw — do NOT copy it into the image):
        {question_text}

        Return ONLY the Python code. No explanation. No markdown fences.
    """).strip()


def generate_question_image(question_text: str, options: dict) -> str | None:
    """
    Ask Claude to write matplotlib code for the question, execute it locally,
    and return the path to the saved PNG.  Results are cached on disk.

    Returns a file path string on success, or None on any failure.
    """
    if not ENABLE_IMAGE_GENERATION:
        return None
    if not _needs_image(question_text, options):
        return None

    cache = _cache_path(question_text)
    if os.path.exists(cache):
        return cache

    # ── Step 1: ask Claude to write the matplotlib code ───────────────────
    prompt = _build_code_prompt(question_text, options)
    try:
        response = _claude.messages.create(
            model="claude-haiku-4-5-20251001",   # fast + cheap; Haiku is fine for code gen
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        time.sleep(API_CALL_DELAY)

        raw_code = ""
        for block in response.content:
            if hasattr(block, "text"):
                raw_code += block.text

        # Strip any accidental markdown fences Claude may have included
        raw_code = re.sub(r"```(?:python)?", "", raw_code).replace("```", "").strip()

        if not raw_code:
            print(f"    ⚠️  Claude returned no code for: {question_text[:60]}...")
            return None

    except Exception as e:
        print(f"    ⚠️  Claude API call failed: {e}")
        return None

    # ── Step 2: execute the code in an isolated namespace ─────────────────
    # We inject OUTPUT_PATH so the generated code knows where to save.
    exec_globals: dict = {
        "__builtins__": __builtins__,
        "OUTPUT_PATH": cache,
    }
    try:
        import matplotlib
        matplotlib.use("Agg")   # non-interactive backend — no display needed
        import matplotlib.pyplot as plt
        exec_globals["plt"] = plt
        exec_globals["matplotlib"] = matplotlib

        exec(raw_code, exec_globals)   # noqa: S102

        if os.path.exists(cache):
            plt.close("all")           # release memory
            return cache
        else:
            print(f"    ⚠️  Code ran but no PNG was saved for: {question_text[:60]}...")
            return None

    except Exception:
        print(f"    ⚠️  Generated code failed to execute for: {question_text[:60]}...")
        print(textwrap.indent(traceback.format_exc(), "        "))
        # Attempt a second pass with the error included so Claude can fix it
        return _retry_with_error(question_text, options, raw_code, cache)


def _retry_with_error(question_text: str, options: dict,
                      bad_code: str, cache: str) -> str | None:
    """
    If the first attempt's code raised an exception, send Claude the traceback
    and ask it to fix the code.  One retry only.
    """
    err_text = traceback.format_exc()
    fix_prompt = textwrap.dedent(f"""
        The following matplotlib code raised an error when executed.
        Fix the code so it runs without errors.  Apply the same rules as before
        (save to OUTPUT_PATH, no plt.show, white background, 4×3 inches at 100 dpi).
        Return ONLY corrected Python code, no explanation, no markdown fences.

        --- Original code ---
        {bad_code}

        --- Error ---
        {err_text}
    """).strip()

    try:
        response = _claude.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": fix_prompt}],
        )
        time.sleep(API_CALL_DELAY)

        fixed_code = ""
        for block in response.content:
            if hasattr(block, "text"):
                fixed_code += block.text
        fixed_code = re.sub(r"```(?:python)?", "", fixed_code).replace("```", "").strip()

        if not fixed_code:
            return None

        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        exec_globals: dict = {
            "__builtins__": __builtins__,
            "OUTPUT_PATH": cache,
            "plt": plt,
            "matplotlib": matplotlib,
        }
        exec(fixed_code, exec_globals)   # noqa: S102
        plt.close("all")
        return cache if os.path.exists(cache) else None

    except Exception as e:
        print(f"    ⚠️  Retry also failed: {e}")
        return None



# ============================================================
# === JSON parsing helpers ===
# ============================================================
def detect_encoding(file_path):
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
    data_list = []
    encoding = detect_encoding(file_path)
    with open(file_path, "r", encoding=encoding) as f:
        try:
            content = json.load(f)
            decoded_content = decode_unicode_escapes(content)
            if isinstance(decoded_content, list):
                data_list.extend(decoded_content)
            elif isinstance(decoded_content, dict):
                for key in ("questions", "data", "items"):
                    if key in decoded_content and isinstance(decoded_content[key], list):
                        data_list.extend(decoded_content[key])
                        break
                else:
                    data_list.append(decoded_content)
        except Exception as e:
            print(f"⚠️ Failed to parse {file_path}: {e}")
    print(f"✅ Parsed {len(data_list)} total questions.")
    return data_list


def get_options(item):
    opts = item.get("options", {}) or {}
    while isinstance(opts, dict) and "options" in opts and isinstance(opts["options"], dict):
        opts = opts["options"]
    return opts


def question_signature(q):
    try:
        q_str = json.dumps(q, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(q_str.encode("utf-8")).hexdigest()
    except Exception:
        return str(id(q))


def is_in(value, allowed):
    if isinstance(allowed, (list, tuple, set)):
        return value in allowed
    return value == allowed


# ============================================================
# === Question selection ===
# ============================================================
def select_questions(all_data, used, filters, count):
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
# === PDF page callbacks ===
# ============================================================

COPYRIGHT_TEXT = "© 2026 examGenome.com. All rights reserved."
FOOTER_Y       = MARGIN_OUTER - 18   # just inside the bottom margin


def _draw_copyright_footer(canvas_obj, doc):
    """
    Draw the copyright notice at the bottom of every content page (page 3+).
    Also draws the faint watermark logo behind the content.
    """
    # Watermark
    canvas_obj.saveState()
    canvas_obj.setFillAlpha(0.05)
    try:
        watermark = ImageReader(LOGO_PATH)
        wm = 900
        canvas_obj.drawImage(
            watermark,
            (PAGE_WIDTH - wm) / 2, (PAGE_HEIGHT - wm) / 2,
            width=wm, height=wm,
            preserveAspectRatio=True, mask="auto",
        )
    except Exception:
        pass
    canvas_obj.restoreState()

    # Copyright footer
    canvas_obj.saveState()
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(colors.HexColor("#555555"))
    canvas_obj.drawCentredString(PAGE_WIDTH / 2, FOOTER_Y, COPYRIGHT_TEXT)
    canvas_obj.restoreState()


# ============================================================
# === Question block builder (text + optional image side by side) ===
# ============================================================

def build_question_block(idx: int, question_text: str, opts: dict,
                         content_style, body_style,
                         img_path: str | None) -> list:
    """
    Return a list of ReportLab flowables that render one question.

    Layout when an image is available:
    ┌──────────────────────────────────┬──────────────────┐
    │  Q. question text                │                  │
    │  A: option text                  │   [diagram]      │
    │  B: option text                  │                  │
    │  C: option text                  │                  │
    │  D: option text                  │                  │
    └──────────────────────────────────┴──────────────────┘

    Layout when no image:
    Q. question text
    A: option text   B: option text
    C: option text   D: option text
    """
    usable_width = PAGE_WIDTH - 2 * (MARGIN_OUTER + INNER_MARGIN)  # ≈ 435pt

    if img_path and os.path.exists(img_path):
        # ── Two-column layout: text left, image right ──────────────────────
        text_col_width = usable_width - IMAGE_PDF_WIDTH - 8   # 8pt gap

        # Build left-column content as a nested table of paragraphs
        left_items = [Paragraph(f"<b>{idx}.</b> {question_text}", content_style)]
        left_items.append(Spacer(1, 4))
        for opt_key, opt_val in opts.items():
            left_items.append(Paragraph(f"{opt_key}: {opt_val}", body_style))

        # Stack left-column items into a single-column sub-table so we can
        # place them alongside the image in an outer two-column table.
        left_table = Table(
            [[item] for item in left_items],
            colWidths=[text_col_width],
        )
        left_table.setStyle(TableStyle([
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ]))

        # Image cell
        img_flowable = Image(img_path, width=IMAGE_PDF_WIDTH, height=IMAGE_PDF_HEIGHT,
                             kind="proportional")

        outer = Table(
            [[left_table, img_flowable]],
            colWidths=[text_col_width + 4, IMAGE_PDF_WIDTH + 4],
        )
        outer.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ]))

        return [KeepTogether([outer, Spacer(1, 14)])]

    else:
        # ── Original single-column layout ─────────────────────────────────
        items = []
        items.append(Paragraph(f"<b>{idx}.</b> {question_text}", content_style))
        items.append(Spacer(1, 6))
        for opt_key, opt_val in opts.items():
            items.append(Paragraph(f"{opt_key}: {opt_val}", content_style))
        items.append(Spacer(1, 12))
        return items


# ============================================================
# === PDF merging — prepend cover pages ===
# ============================================================

# Paths to the pre-made cover pages (expected alongside this script).
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
FIRST_PAGE   = os.path.join(SCRIPT_DIR, "Year_3_Geometry_Properties_of_Shapes_Worksheet.pdf")
SECOND_PAGE  = os.path.join(SCRIPT_DIR, "Year_3_Geometry_Properties_of_Shapes_Guide.pdf")


def _merge_with_cover_pages(content_pdf: str) -> None:
    """
    Prepend firstPage.pdf and secondPage.pdf to the generated content PDF.
    The result overwrites content_pdf in-place.

    If either cover PDF is missing, a warning is printed and the content PDF
    is left unchanged (so generation is never blocked by missing covers).
    """
    writer = PdfWriter()

    for cover_path, label in [(FIRST_PAGE, "firstPage.pdf"),
                               (SECOND_PAGE, "secondPage.pdf")]:
        if os.path.exists(cover_path):
            reader = PdfReader(cover_path)
            for page in reader.pages:
                writer.add_page(page)
            print(f"  📄  Prepended {label}")
        else:
            print(f"  ⚠️  {label} not found at {cover_path} — skipping cover page")

    # Append all content pages
    content_reader = PdfReader(content_pdf)
    for page in content_reader.pages:
        writer.add_page(page)

    # Overwrite the content PDF with the merged result
    with open(content_pdf, "wb") as f:
        writer.write(f)
    print(f"  ✅  Cover pages merged into {content_pdf}")


# ============================================================
# === PDF writing ===
# ============================================================
def write_to_pdf(data_list, output_pdf):
    """Write parsed question data to a PDF file with a formatted answer sheet."""

    # ── Pre-generate images for all questions before building the PDF ──────
    # We do this upfront so the time spent calling Claude doesn't interleave
    # with ReportLab's PDF assembly.
    img_paths: dict[int, str | None] = {}   # idx (1-based) → image file path or None

    if ENABLE_IMAGE_GENERATION:
        print(f"  🖼️  Generating diagrams for {len(data_list)} questions...")
        for idx, entry in enumerate(data_list, start=1):
            numbers = entry.get("numbers")
            if isinstance(numbers, list) and len(numbers) > 0:
                img_paths[idx] = None
            else:
                q_text = entry.get("question", "")
                opts   = get_options(entry)
                path   = generate_question_image(q_text, opts)
                # Req 3: on any generation failure, path is None → no layout reserved
                img_paths[idx] = path
                if path:
                    print(f"    ✅ Q{idx}: diagram saved → {os.path.basename(path)}")
    else:
        img_paths = {idx: None for idx in range(1, len(data_list) + 1)}

    # ── Build PDF (questions + answer sheet only, no first/second page) ──────
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        leftMargin=MARGIN_OUTER + INNER_MARGIN,
        rightMargin=MARGIN_OUTER + INNER_MARGIN,
        topMargin=MARGIN_OUTER + INNER_MARGIN,
        bottomMargin=MARGIN_OUTER + INNER_MARGIN + 16,   # extra space for footer
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
    content_style = ParagraphStyle(
        "Content", parent=styles["Normal"], fontSize=11, spaceAfter=12
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"], fontSize=11, spaceAfter=6
    )

    # ── Main Question Section ───────────────────────────────────────────────
    story.append(Paragraph("Questions", title_style))
    story.append(Spacer(1, 12))

    for idx, entry in enumerate(data_list, start=1):
        numbers = entry.get("numbers")

        if isinstance(numbers, list) and len(numbers) > 0:
            # Grouped question — keep original layout (no image)
            sub_questions = entry.get("questions", [])
            story.append(Paragraph(f"<b>{idx}.</b> {numbers}", body_style))
            story.append(Spacer(1, 10))
            for sub_idx, sub_item in enumerate(sub_questions, start=1):
                sub_label = f"({chr(96 + sub_idx)})"
                q    = sub_item.get("question", "N/A")
                opts = get_options(sub_item)
                story.append(Paragraph(f"{sub_label}: {q}", body_style))
                story.append(Spacer(1, 4))
                for opt_key, opt_val in opts.items():
                    story.append(Paragraph(f"{opt_key}: {opt_val}", body_style))
                story.append(Spacer(1, 10))
        else:
            # Standalone question — use two-column layout if image available
            q_text   = entry.get("question", "N/A")
            opts     = get_options(entry)
            img_path = img_paths.get(idx)

            block = build_question_block(idx, q_text, opts,
                                         content_style, body_style, img_path)
            story.extend(block)

    story.append(PageBreak())

    # ── Answer Sheet Section ────────────────────────────────────────────────
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
        answer_table.setStyle(TableStyle([
            ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME",     (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE",     (0, 0), (-1, -1), 10),
            ("INNERGRID",    (0, 0), (-1, -1), 0.25, colors.grey),
            ("BOX",          (0, 0), (-1, -1), 0.25, colors.grey),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
            ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ]))
        story.append(answer_table)
        story.append(Spacer(1, 12))

    doc.build(story,
              onFirstPage=_draw_copyright_footer,
              onLaterPages=_draw_copyright_footer)

    # ── Merge firstPage.pdf + secondPage.pdf + content PDF ─────────────────
    _merge_with_cover_pages(output_pdf)
    print(f"✅ Created PDF: {output_pdf} ({len(data_list)} questions)")


# ============================================================
# === PDF batching / orchestration ===
# ============================================================
def create_multiple_pdfs(all_data):
    total_questions = len(all_data)
    if total_questions == 0:
        print("❌ No data to process.")
        return

    num_pdfs = ceil(total_questions / TOTAL_PER_PDF)
    print(f"📦 Found {total_questions} total questions → will attempt up to {num_pdfs} PDFs")

    used_questions = set()

    has_difficulty = any(q.get("difficulty") for q in all_data)
    if not has_difficulty:
        print(
            "ℹ️ No 'difficulty' field found on any question — "
            "selecting questions purely at random instead of by difficulty."
        )

    for i in range(num_pdfs):
        print(f"\n🧮 Preparing PDF {i + 1}...")

        if has_difficulty:
            section1 = select_questions(all_data, used_questions, {"difficulty": "easy"},   QUESTIONS_PER_DIFFICULTY)
            section2 = select_questions(all_data, used_questions, {"difficulty": "medium"}, QUESTIONS_PER_DIFFICULTY)
            section3 = select_questions(all_data, used_questions, {"difficulty": "hard"},   QUESTIONS_PER_DIFFICULTY)
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
        sample_keys = set(all_data[0].keys())
        print(f"🔍 Sample question keys: {sample_keys}")

        diff_counts = Counter(q.get("difficulty", "MISSING") for q in all_data)
        print(f"🔍 Difficulty distribution: {dict(diff_counts)}")

        create_multiple_pdfs(all_data)
