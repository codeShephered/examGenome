import os
import json
import random
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

# === Configuration ===
INPUT_FOLDER = "qBaseJson"   # folder where your *.json files are stored
OUTPUT_PDF = "questions_output_enh.pdf"

# === Classification types ===
CLASSIFICATIONS = [
    "Algebra",
    "Arithmetic",
    "Combinatorics",
    "Decimals",
    "Fractions",
    "Geometry",
    "Measurement",
    "Percentages",
    "Probability",
    "Ratio & Proportion",
    "Set theory",
    "Speed, Distance & Time",
    "Statistics"
]

MAX_PER_TYPE = 4
TOTAL_QUESTIONS = 50


def parse_json_files(folder_path):
    """Parse all *.json files from the folder and return list of dicts."""
    data_list = []
    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    content = json.load(f)
                    if isinstance(content, dict):
                        data_list.append(content)
                    elif isinstance(content, list):
                        data_list.extend(content)
                except Exception as e:
                    print(f"⚠️ Failed to parse {filename}: {e}")
    return data_list


def filter_and_sample_questions(data_list):
    """Randomly select up to TOTAL_QUESTIONS, max 4 per classification."""
    selected_questions = []
    type_count = {t: 0 for t in CLASSIFICATIONS}

    # Shuffle the input to ensure randomness
    random.shuffle(data_list)

    for item in data_list:
        qtype = item.get("type", "").strip()
        # Match against known classifications (case-insensitive)
        for cls in CLASSIFICATIONS:
            if qtype.lower().startswith(cls.lower()) and type_count[cls] < MAX_PER_TYPE:
                selected_questions.append(item)
                type_count[cls] += 1
                break

        # Stop when we reach the total required
        if len(selected_questions) >= TOTAL_QUESTIONS:
            break

    print(f"✅ Selected {len(selected_questions)} questions")
    print("📊 Type distribution:")
    for cls, count in type_count.items():
        if count > 0:
            print(f"  - {cls}: {count}")
    return selected_questions


def write_to_pdf(data_list, output_pdf):
    """Write parsed JSON data to a PDF file."""
    doc = SimpleDocTemplate(output_pdf, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    for idx, item in enumerate(data_list, start=1):
        q = item.get("question", "N/A")
        ans = item.get("answer", "N/A")
        opts = item.get("options", {})
        diff = item.get("difficulty", "N/A")
        qtype = item.get("type", "N/A")

        # Question number + classification
        story.append(Paragraph(f"<b>{idx}.</b> {q}", styles["Normal"]))
        story.append(Spacer(1, 6))

        # Options
        for opt_key, opt_val in opts.items():
            story.append(Paragraph(f"{opt_key}: {opt_val}", styles["Normal"]))
        story.append(Spacer(1, 6))

        # Answer + difficulty
        story.append(Paragraph(f"<b>Answer:</b> {ans}", styles["Normal"]))
        story.append(Paragraph(f"<b>Difficulty:</b> {diff}", styles["Normal"]))
        story.append(Spacer(1, 12))

    doc.build(story)


if __name__ == "__main__":
    # Parse all JSON files
    all_data = parse_json_files(INPUT_FOLDER)
    if not all_data:
        print("No valid JSON files found.")
    else:
        # Apply classification and random limits
        selected_data = filter_and_sample_questions(all_data)

        # Generate PDF
        write_to_pdf(selected_data, OUTPUT_PDF)
        print(f"✅ PDF created: {OUTPUT_PDF}")
