#!/usr/bin/env python3
"""
generate_proper_noun_pdfs.py

Reads the Proper Noun worksheets JSON (top-level "worksheets" list, each
with "pdf_number", "topic", "focus_area", "explanation", "examples" and a
"questions" list of {question_number, difficulty, question_text, answer,
explanation}) and writes one PDF per worksheet.

Each PDF contains:
    Cover page      -- firstPage.pdf, prepended unmodified as page 1, IF
                        that file is found next to this script (see
                        below). Every page this script generates then
                        follows from page 2 onward.
    Topic: <topic>
    <focus_area>

    <explanation>

    Examples:
        - each worked example

    Questions:
        <question_number>: <question_text>   (repeated for every question,
                                                each with a two-line-tall
                                                answer box)
    --- new page ---
    Answer Sheet
        <question_number>: <answer>           (repeated for every question)

Every generated page (not the prepended cover) carries a faint watermark
-- the examgenome.png logo, drawn at 80% of the page's width AND 80% of
the page's height (falls back to plain text if the logo is unavailable)
-- plus a footer with the copyright notice (centred) and the page number
(right-aligned).

Usage:
    python3 generate_proper_noun_pdfs.py [input.json] [output_dir] [--logo path.png] [--first-page path.pdf] [--watermark-text "TEXT"] [--watermark-opacity 0.12] [--watermark-size 0.8]

    input.json      Path to the worksheets JSON file.
                     Defaults to "Year3-Proper-Noun-5-Worksheets.json" in
                     the current directory if omitted.
    output_dir      Directory to write the PDFs into (created if missing).
                     Defaults to "proper_noun_pdfs" if omitted.
    --logo PATH     Path to a logo image (PNG/JPG) to use as the watermark.
                     Defaults to "examgenome.png" sitting next to this
                     script, so keep that file alongside the script.
                     Pass --logo '' to disable the image and fall back to
                     a plain text watermark.
    --first-page PATH
                     Path to a poster/cover-page PDF to prepend as page 1.
                     Defaults to "firstPage.pdf" sitting next to this
                     script. Pass --first-page '' to disable prepending.
    --watermark-text "TEXT"
                     Text used as the watermark if no logo image is found.
                     Defaults to "examgenome".
    --watermark-opacity FLOAT
                     Watermark opacity, 0 (invisible) to 1 (solid).
                     Defaults to 0.12 (a faint background mark).
    --watermark-size FLOAT
                     Watermark size as a fraction of the page width AND
                     page height (independently — not aspect-preserving).
                     Defaults to 0.8 (80% x 80%).

Requires: reportlab, Pillow, numpy, pypdf
    (pip install reportlab Pillow numpy pypdf --break-system-packages)
"""

import json
import os
import re
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Flowable,
    KeepTogether,
    ListFlowable,
    ListItem,
)


# ----------------------------------------------------------------------
# A custom flowable: a light-shaded rectangle, used as blank answer space.
# ----------------------------------------------------------------------
class AnswerBox(Flowable):
    """A light grey, rounded-corner rectangle that gives the pupil space
    to write their answer. Behaves as a normal flowable, so it flows and
    paginates correctly inside a Platypus document."""

    def __init__(self, width, height,
                 fill_color=colors.Color(0.93, 0.93, 0.93),
                 border_color=colors.Color(0.70, 0.70, 0.70)):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.fill_color = fill_color
        self.border_color = border_color

    def wrap(self, available_width, available_height):
        return (self.width, self.height)

    def draw(self):
        self.canv.saveState()
        self.canv.setFillColor(self.fill_color)
        self.canv.setStrokeColor(self.border_color)
        self.canv.setLineWidth(0.75)
        self.canv.roundRect(0, 0, self.width, self.height, 3 * mm, fill=1, stroke=1)
        self.canv.restoreState()
# Two lines' worth of handwriting space, with comfortable padding.
TWO_LINE_BOX_HEIGHT = 24 * mm

COPYRIGHT_TEXT = "\u00a9 2026 ExamGenome.com. All rights reserved."


def draw_footer(canvas_obj, doc):
    """Draw the copyright notice (centred) and page number (bottom
    right) in the page footer. The page number reflects position within
    this reportlab-generated document only (1, 2, 3, ...) -- it does not
    account for a cover page prepended afterwards by pypdf."""
    canvas_obj.saveState()
    page_width, _ = doc.pagesize
    footer_y = 10 * mm
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(colors.Color(0.35, 0.35, 0.35))
    canvas_obj.drawCentredString(page_width / 2, footer_y, COPYRIGHT_TEXT)
    canvas_obj.drawRightString(page_width - 20 * mm, footer_y, f"Page {canvas_obj.getPageNumber()}")
    canvas_obj.restoreState()


# ----------------------------------------------------------------------
# Watermark support
# ----------------------------------------------------------------------
def prepare_watermark_image(source_path, cache_path, opacity=0.12, white_threshold=240):
    """Take a logo PNG (typically opaque, white background) and produce a
    faded, background-removed version suitable for use as a watermark:
    - Near-white pixels become fully transparent.
    - Every remaining pixel's alpha is scaled down to `opacity`, so the
      logo reads as a faint background mark rather than a bold overlay.

    The result is cached to `cache_path` and only rebuilt if missing, so
    repeated calls (one per PDF) do not reprocess the image each time.
    """
    if os.path.isfile(cache_path):
        return cache_path

    from PIL import Image
    import numpy as np

    img = Image.open(source_path).convert("RGBA")
    arr = np.array(img)

    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    is_white = (r >= white_threshold) & (g >= white_threshold) & (b >= white_threshold)

    max_alpha = int(255 * opacity)
    arr[..., 3] = np.where(is_white, 0, max_alpha)

    Image.fromarray(arr, "RGBA").save(cache_path)
    return cache_path


def draw_watermark(canvas_obj, doc, text="examgenome", logo_path=None,
                    opacity=0.12, font_size=60, rotation=0,
                    text_color=colors.grey,
                    size_fraction=0.8):
    """Draw a diagonal watermark on the current page, behind whatever
    content is about to be drawn on top of it.

    If `logo_path` is given, it is expected to already be a prepared
    (background-removed, faded) image — see `prepare_watermark_image`.
    The image is drawn at `size_fraction` of the page WIDTH and
    `size_fraction` of the page HEIGHT independently (so at the default
    0.8 that is 80% of the page's width and 80% of the page's height,
    exactly as specified — not aspect-ratio preserving).

    If no logo is available, falls back to a semi-transparent text
    watermark instead.
    """
    canvas_obj.saveState()

    page_width, page_height = doc.pagesize
    canvas_obj.translate(page_width / 2, page_height / 2)
    canvas_obj.rotate(rotation)

    if logo_path and os.path.isfile(logo_path):
        from reportlab.lib.utils import ImageReader
        img = ImageReader(logo_path)
        target_width = page_width * size_fraction
        target_height = page_height * size_fraction
        canvas_obj.drawImage(
            img,
            -target_width / 2, -target_height / 2,
            width=target_width, height=target_height,
            mask="auto",
        )
    else:
        canvas_obj.setFillAlpha(opacity)
        canvas_obj.setFont("Helvetica-Bold", font_size)
        canvas_obj.setFillColor(text_color)
        canvas_obj.drawCentredString(0, 0, text)

    canvas_obj.restoreState()


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def slugify(title):
    """Turn a title into a safe filename."""
    slug = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_")
    slug = re.sub(r"_+", "_", slug)
    return slug or "worksheet"


def build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name= "TopicTitle", parent=styles["Title"],
        fontSize=18, leading=22, spaceAfter=2 * mm,
    ))
    styles.add(ParagraphStyle(
        name="FocusArea", parent=styles["Heading2"],
        fontSize=14, leading=17, spaceAfter=4 * mm,
        textColor=colors.Color(0.30, 0.30, 0.30), alignment=1,  # centred
    ))
    styles.add(ParagraphStyle(
        name="ExplanationText", parent=styles["BodyText"],
        fontSize=11, leading=15, spaceAfter=4 * mm,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading", parent=styles["Heading2"],
        fontSize=13, leading=16, spaceBefore=4 * mm, spaceAfter=3 * mm,
        textColor=colors.Color(0.10, 0.10, 0.40),
    ))
    styles.add(ParagraphStyle(
        name="ExampleText", parent=styles["BodyText"],
        fontSize=11, leading=15, spaceAfter=1.5 * mm,
    ))
    styles.add(ParagraphStyle(
        name="QuestionText", parent=styles["BodyText"],
        fontSize=11, leading=15, spaceBefore=2 * mm, spaceAfter=1.5 * mm,
    ))
    styles.add(ParagraphStyle(
        name="DifficultyTag", parent=styles["BodyText"],
        fontSize=8.5, leading=10, textColor=colors.Color(0.45, 0.45, 0.45),
        spaceAfter=1 * mm,
    ))
    styles.add(ParagraphStyle(
        name="SheetText", parent=styles["BodyText"],
        fontSize=11, leading=15, spaceBefore=1 * mm, spaceAfter=3 * mm,
    ))
    return styles


def build_worksheet_pdf(worksheet, output_path, page_size=A4,
                         watermark_text="examgenome", logo_path=None,
                         watermark_size_fraction=0.8):
    """Build a single Proper Noun worksheet PDF."""
    styles = build_styles()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=page_size,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=22 * mm,
        title=f"{worksheet['topic']} - {worksheet['focus_area']}",
    )
    usable_width = doc.width

    story = []

    # ---- Topic and focus area ----
    story.append(Paragraph(f"{worksheet['topic']}", styles["TopicTitle"]))
    story.append(Paragraph(worksheet["focus_area"], styles["FocusArea"]))

    # ---- Explanation ----
    story.append(Paragraph(worksheet["explanation"], styles["ExplanationText"]))

    # ---- Examples ----
    story.append(Paragraph("Examples:", styles["SectionHeading"]))
    example_items = [
        ListItem(Paragraph(ex, styles["ExampleText"]), leftIndent=4 * mm)
        for ex in worksheet["examples"]
    ]
    story.append(ListFlowable(example_items, bulletType="bullet", start="circle"))

    # ---- Questions, each with blank space to answer ----
    story.append(Paragraph("Questions:", styles["SectionHeading"]))

    for q in worksheet["questions"]:
        q_number = q["question_number"]
        q_text = q["question_text"]
        difficulty = q.get("difficulty", "")

        block = [Paragraph(f"<b>{q_number}:</b> {q_text}", styles["QuestionText"])]
        if difficulty:
            block.append(Paragraph(f"({difficulty})", styles["DifficultyTag"]))
        block.append(AnswerBox(width=usable_width, height=TWO_LINE_BOX_HEIGHT))
        block.append(Spacer(1, 2 * mm))

        # Keep each question together with its answer box so it is never
        # split across a page break.
        story.append(KeepTogether(block))

    # ---- Answer Sheet (new page) ----
    story.append(PageBreak())
    story.append(Paragraph(f"{worksheet['topic']}", styles["TopicTitle"]))
    story.append(Paragraph(worksheet["focus_area"], styles["FocusArea"]))
    story.append(Paragraph("Answer Sheet", styles["SectionHeading"]))

    for q in worksheet["questions"]:
        story.append(Paragraph(f"<b>{q['question_number']}.</b> {q['answer']}", styles["SheetText"]))

    def _on_page(canvas_obj, doc_obj):
        draw_watermark(canvas_obj, doc_obj, text=watermark_text, logo_path=logo_path,
                        size_fraction=watermark_size_fraction)
        draw_footer(canvas_obj, doc_obj)

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)


def prepend_cover_page(content_pdf_path, first_page_pdf_path, output_path):
    """Write `output_path` as first_page_pdf_path's pages followed by
    content_pdf_path's pages, unmodified. If first_page_pdf_path is
    falsy or missing, output_path is just a copy of content_pdf_path."""
    from pypdf import PdfReader, PdfWriter

    writer = PdfWriter()
    if first_page_pdf_path and os.path.isfile(first_page_pdf_path):
        for page in PdfReader(first_page_pdf_path).pages:
            writer.add_page(page)
    for page in PdfReader(content_pdf_path).pages:
        writer.add_page(page)
    with open(output_path, "wb") as f:
        writer.write(f)


def main():
    import argparse

    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_logo = os.path.join(script_dir, "examgenome.png")
    default_first_page = os.path.join(script_dir, "Year_3_Proper_Noun_Worksheet.pdf")

    parser = argparse.ArgumentParser(
        description="Generate one Proper Noun worksheet PDF per topic "
                     "(worksheet + answer sheet), with a logo watermark "
                     "and copyright/page-number footer on every "
                     "generated page."
    )
    parser.add_argument("input_json", nargs="?", default="Year3-Proper-Noun-5-Worksheets.json",
                         help="Path to the worksheets JSON file.")
    parser.add_argument("output_dir", nargs="?", default="proper_noun_pdfs",
                         help="Directory to write the PDFs into.")
    parser.add_argument("--logo", default=default_logo,
                         help="Path to a logo image (PNG/JPG) to use as the watermark. "
                              "Defaults to 'examgenome.png' next to this script. "
                              "Pass --logo '' to disable and use a text watermark instead.")
    parser.add_argument("--first-page", default=default_first_page,
                         help="Path to a poster/cover-page PDF to prepend as page 1. "
                              "Defaults to 'firstPage.pdf' next to this script. "
                              "Pass --first-page '' to disable prepending.")
    parser.add_argument("--watermark-text", default="examgenome",
                         help="Text to use as the watermark when no logo image is available "
                              "(default: 'examgenome').")
    parser.add_argument("--watermark-opacity", type=float, default=0.12,
                         help="Watermark opacity from 0 (invisible) to 1 (solid). Default: 0.12.")
    parser.add_argument("--watermark-size", type=float, default=0.8,
                         help="Watermark size as a fraction of the page width AND height "
                              "(default: 0.8, i.e. 80%% of each).")
    args = parser.parse_args()

    input_path = args.input_json
    output_dir = args.output_dir

    if not os.path.isfile(input_path):
        print(f"Error: input file not found: {input_path}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    logo_path = None
    if args.logo and os.path.isfile(args.logo):
        cache_path = os.path.join(output_dir, ".watermark_cache.png")
        logo_path = prepare_watermark_image(args.logo, cache_path, opacity=args.watermark_opacity)
        print(f"Using logo watermark: {args.logo} (size: {args.watermark_size*100:.0f}% x {args.watermark_size*100:.0f}% of page)")
    elif args.logo:
        print(f"Warning: logo file not found at '{args.logo}'. Falling back to text watermark.")

    first_page_path = args.first_page if args.first_page and os.path.isfile(args.first_page) else None
    if args.first_page and not first_page_path:
        print(f"Warning: cover page file not found at '{args.first_page}'. "
              f"Generating PDFs WITHOUT a cover page. Add a file at that path to enable it.")
    elif first_page_path:
        print(f"Using cover page: {first_page_path}")

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    worksheets = data.get("worksheets", [])
    if not worksheets:
        print("Error: no worksheets found in the JSON file.")
        sys.exit(1)

    written = []
    for i, worksheet in enumerate(worksheets, 1):
        required_keys = {"topic", "focus_area", "explanation", "examples", "questions"}
        if not required_keys.issubset(worksheet.keys()):
            print(f"Skipping worksheet {i}: missing one of {required_keys}")
            continue

        slug = slugify(worksheet["focus_area"])
        filename = f"{i:02d}_{slug}.pdf"
        output_path = os.path.join(output_dir, filename)

        content_path = os.path.join(output_dir, f".content_{i:02d}.pdf")
        build_worksheet_pdf(worksheet, content_path,
                             watermark_text=args.watermark_text,
                             logo_path=logo_path,
                             watermark_size_fraction=args.watermark_size)

        prepend_cover_page(content_path, first_page_path, output_path)
        os.remove(content_path)

        written.append(output_path)
        print(f"Written: {output_path}  ({len(worksheet['questions'])} questions)")

    print(f"\nDone. {len(written)} PDF worksheet(s) written to '{output_dir}/'.")


if __name__ == "__main__":
    main()
