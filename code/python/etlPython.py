import os
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

# === Configuration ===
INPUT_FOLDER = "qBaseJson"   # folder where your *.json files are stored
OUTPUT_PDF = "questions_output.pdf"

def parse_json_files(folder_path):
    """Parse all *.json files from the folder and return list of dicts."""
    data_list = []
    for filename in sorted(os.listdir(folder_path)):
        print("FILENAME:"+filename)
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    # Some files might contain multiple objects or arrays
                    content = json.load(f)
                    if isinstance(content, dict):
                        data_list.append(content)
                    elif isinstance(content, list):
                        data_list.extend(content)
                except Exception as e:
                    print(f"⚠️ Failed to parse {filename}: {e}")
    return data_list

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
        
        # Question number + text
        story.append(Paragraph(f"<b>{idx}. {q}</b>", styles["Normal"]))
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
    # Parse JSON files
    all_data = parse_json_files(INPUT_FOLDER)
    if not all_data:
        print("No valid JSON files found.")
    else:
        write_to_pdf(all_data, OUTPUT_PDF)
        print(f"✅ PDF created: {OUTPUT_PDF}")
