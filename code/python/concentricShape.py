import random
import json
import math
import os
import matplotlib
matplotlib.use("Agg")  # Safe for servers / no GUI
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Parameters
questionVolume = 20
output_file = "geometry_questions.json"
img_dir = "geometry_images"
os.makedirs(img_dir, exist_ok=True)

# Difficulty ranges for dimensions
difficulty_ranges = {
    "easy": (5, 15),
    "medium": (15, 30),
    "difficult": (30, 60)
}

# Shape types
shape_types = [
    "circle_in_square",
    "triangle_in_square",
    "square_in_rectangle",
    "triangle_in_rectangle",
    "circle_in_rectangle"
]

def generate_question(shape_type, difficulty, qid):
    low, high = difficulty_ranges[difficulty]

    if shape_type == "circle_in_square":
        side = random.randint(low, high)
        radius = side / 3   # fixed ratio
        outer_area = side**2
        inner_area = math.pi * radius**2
        question = f"A circle of radius {radius:.1f} cm is drawn inside a square of side {side} cm. What is the shaded area?"

    elif shape_type == "triangle_in_square":
        side = random.randint(low, high)
        base = side
        height = side
        inner_area = 0.5 * base * height
        outer_area = side**2
        question = f"A triangle with base {base} cm and height {height} cm is inside a square of side {side} cm. What is the shaded area?"

    elif shape_type == "square_in_rectangle":
        rect_w = random.randint(low, high)
        rect_h = random.randint(low, high)
        inner_side = min(rect_w, rect_h) // 2
        outer_area = rect_w * rect_h
        inner_area = inner_side**2
        question = f"A square of side {inner_side} cm is inside a rectangle of {rect_w}×{rect_h} cm. What is the shaded area?"

    elif shape_type == "triangle_in_rectangle":
        rect_w = random.randint(low, high)
        rect_h = random.randint(low, high)
        base = rect_w
        height = rect_h // 2
        inner_area = 0.5 * base * height
        outer_area = rect_w * rect_h
        question = f"A triangle with base {base} cm and height {height} cm is inside a rectangle of {rect_w}×{rect_h} cm. What is the shaded area?"

    elif shape_type == "circle_in_rectangle":
        rect_w = random.randint(low, high)
        rect_h = random.randint(low, high)
        radius = min(rect_w, rect_h) / 4
        inner_area = math.pi * radius**2
        outer_area = rect_w * rect_h
        question = f"A circle of radius {radius:.1f} cm is inside a rectangle of {rect_w}×{rect_h} cm. What is the shaded area?"

    # Shaded area
    shaded_area = outer_area - inner_area
    correct = round(shaded_area, 1)

    # Generate options labeled A–E
    option_values = [correct]
    while len(option_values) < 5:
        fake = round(correct + random.uniform(-0.3 * correct, 0.3 * correct), 1)
        if fake > 0 and fake not in option_values:
            option_values.append(fake)
    random.shuffle(option_values)

    options = {label: f"{val} cm²" for label, val in zip("ABCDE", option_values)}
    correct_label = [k for k, v in options.items() if str(correct) in v][0]

    # Draw diagram (standard placement, no randomness in coords)
    fig, ax = plt.subplots()
    if shape_type == "circle_in_square":
        ax.add_patch(patches.Rectangle((0, 0), side, side, color="black"))
        ax.add_patch(patches.Circle((side/2, side/2), radius, color="white"))

    elif shape_type == "triangle_in_square":
        ax.add_patch(patches.Rectangle((0, 0), side, side, color="black"))
        ax.add_patch(patches.Polygon([[0,0],[side,0],[side/2,side]], closed=True, color="white"))

    elif shape_type == "square_in_rectangle":
        ax.add_patch(patches.Rectangle((0, 0), rect_w, rect_h, color="black"))
        ax.add_patch(patches.Rectangle(((rect_w-inner_side)/2, (rect_h-inner_side)/2),
                                       inner_side, inner_side, color="white"))

    elif shape_type == "triangle_in_rectangle":
        ax.add_patch(patches.Rectangle((0, 0), rect_w, rect_h, color="black"))
        ax.add_patch(patches.Polygon([[0,0],[rect_w,0],[rect_w/2,rect_h]], closed=True, color="white"))

    elif shape_type == "circle_in_rectangle":
        ax.add_patch(patches.Rectangle((0, 0), rect_w, rect_h, color="black"))
        ax.add_patch(patches.Circle((rect_w/2, rect_h/2), radius, color="white"))

    ax.set_xlim(0, max(high, high))
    ax.set_ylim(0, max(high, high))
    ax.axis("off")

    img_path = os.path.join(img_dir, f"{shape_type}_{qid}.png")
    plt.savefig(img_path, bbox_inches="tight")
    plt.close()

    return {
        "question": question,
        "options": options,
        "answer": f"{correct_label}. {correct} cm²",
        "img_path": img_path,
        "difficulty": difficulty
    }

# Generate all questions
questions = []
for qid in range(1, questionVolume+1):
    difficulty = random.choice(list(difficulty_ranges.keys()))
    shape_type = random.choice(shape_types)
    questions.append(generate_question(shape_type, difficulty, qid))

# Save to JSON
with open(output_file, "w") as f:
    json.dump(questions, f, indent=2)

print(f"✅ Generated {len(questions)} questions into {output_file}")
