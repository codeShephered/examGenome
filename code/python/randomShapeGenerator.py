#!/usr/bin/env python3
"""
Geometry MCQ Generator
Generates images + JSON for MCQs across shapes and difficulties.

Shapes:
- square, rectangle, equilateral_triangle, isosceles_triangle, scalene_triangle,
  trapezium (isosceles trapezium), parallelogram, circle, regular_hexagon, regular_pentagon

Question types (random per question):
- area, perimeter/circumference, missing dimension (side/width/height/radius/diameter),
  symmetry (excluded for circle which has infinite symmetry)

Difficulties and integer dimension ranges (cm):
- easy: 1–10
- medium: 11–50
- difficult: 51–100

Output:
- Images saved to images/[easy|medium|difficult]/Q#.png
- questions.json with: {question, correct_answer, options, difficulty_level, img_path}

Notes:
- All answer options are integers in string format (no decimals, no mixed numbers).
- Missing dimension is drawn as a dimension line labeled "?" (no units).
- Labels have a white background (bbox) and high z-order so lines never interfere.
"""

import os
import json
import math
import random
from typing import Dict, List, Tuple, Any, Optional

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle

# ---------------- Config ----------------
questionVolume = 10
OUT_JSON = "questions.json"
BASE_IMG_DIR = "images"

# Difficulty ranges (integers, in centimeters)
DIFF_RANGES = {
    "easy": (1, 10),
    "medium": (11, 50),
    "difficult": (51, 100),
}

DIFF_LIST = list(DIFF_RANGES.keys())

# Figure aesthetics
FIGSIZE = (2.5, 2.5)
DPI = 150
PAD = 0.8
LINE_W = 1.6
FS_DIM = 8           # dimension label font size (small)
FS_MISC = 7          # other labels if needed

# Fonts: use DejaVu Sans (bundled with Matplotlib) for reliable glyphs
mpl.rcParams['font.family'] = 'DejaVu Sans'

random.seed()  # set a seed here (e.g., random.seed(42)) for reproducibility if desired


# ---------------- Utility helpers ----------------
def ensure_dirs():
    for d in DIFF_LIST:
        os.makedirs(os.path.join(BASE_IMG_DIR, d), exist_ok=True)


def i2s(n: int) -> str:
    """Integer to string (ensures options and answers are strings)."""
    return str(int(n))


def clamp_int(n: float) -> int:
    """Round to nearest integer."""
    return int(round(n))


def set_tidy_limits(ax, xmin, ymin, xmax, ymax):
    ax.set_aspect("equal")
    ax.set_xlim(xmin - PAD, xmax + PAD)
    ax.set_ylim(ymin - PAD, ymax + PAD)
    ax.axis("off")


def draw_line(ax, x1, y1, x2, y2, **kwargs):
    kwargs.setdefault("color", "black")
    kwargs.setdefault("linewidth", LINE_W)
    kwargs.setdefault("zorder", 1)
    ax.plot([x1, x2], [y1, y2], **kwargs)


def draw_rect(ax, x, y, w, h, **kwargs):
    kwargs.setdefault("edgecolor", "black")
    kwargs.setdefault("linewidth", LINE_W)
    kwargs.setdefault("fill", False)
    kwargs.setdefault("zorder", 1)
    ax.add_patch(Rectangle((x, y), w, h, **kwargs))


def draw_poly(ax, pts, **kwargs):
    kwargs.setdefault("edgecolor", "black")
    kwargs.setdefault("linewidth", LINE_W)
    kwargs.setdefault("fill", False)
    kwargs.setdefault("zorder", 1)
    ax.add_patch(Polygon(pts, closed=True, **kwargs))


def draw_circle(ax, cx, cy, r, **kwargs):
    kwargs.setdefault("edgecolor", "black")
    kwargs.setdefault("linewidth", LINE_W)
    kwargs.setdefault("fill", False)
    kwargs.setdefault("zorder", 1)
    ax.add_patch(Circle((cx, cy), r, **kwargs))


def label_text(ax, x, y, text, rot=0):
    """Text with white bbox and high z-order (foreground)."""
    ax.text(
        x, y, text,
        ha="center", va="center",
        fontsize=FS_DIM, rotation=rot,
        bbox=dict(facecolor="white", edgecolor="none", pad=1.0),
        zorder=10
    )


def draw_dimension(ax, x1, y1, x2, y2, label: Optional[str], offset=0.25):
    """
    Draw a clean dimension line (no inverted T-caps), slightly offset from the
    segment so it doesn't touch the shape border. If label is None, nothing is drawn.
    If label is "?" → draw the dimension line and label "?" (no units).
    If label is "12 cm" → draw that text.

    The line is drawn parallel to the segment, shifted by 'offset'.
    """
    # Direction of segment
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    if L < 1e-9 or label is None:
        return

    # Unit normal to shift the line for clarity
    nx, ny = -dy / L, dx / L

    # Shift both endpoints
    sx1, sy1 = x1 + nx * offset, y1 + ny * offset
    sx2, sy2 = x2 + nx * offset, y2 + ny * offset

    # Draw the dimension line
    draw_line(ax, sx1, sy1, sx2, sy2, zorder=2)

    # Place the label at the midpoint
    mx, my = (sx1 + sx2) / 2.0, (sy1 + sy2) / 2.0
    angle = math.degrees(math.atan2(dy, dx))
    # Label text in foreground with white background
    label_text(ax, mx, my, label, rot=angle if abs(angle) not in (0, 180) else 0)


# ---------------- Option generators ----------------
def mcq_options_int(correct_value: int, spread: int = 8) -> Tuple[Dict[str, str], str]:
    """
    Return options A-E (integer strings) and correct letter. Ensures uniqueness and positivity.
    Spread controls distractor distance around correct.
    """
    correct = int(correct_value)
    labels = ["A", "B", "C", "D", "E"]

    # Gather unique integers around correct
    cand = set([correct])
    # Adjust spread relative to magnitude
    base = max(6, int(round(abs(correct) * 0.2)))
    limit = max(spread, base)
    while len(cand) < 5:
        delta = random.randint(1, limit)
        sign = random.choice([-1, 1])
        val = correct + sign * delta
        if val > 0:
            cand.add(val)

    opts = list(cand)
    random.shuffle(opts)
    correct_letter = labels[opts.index(correct)]
    return {labels[i]: i2s(opts[i]) for i in range(5)}, correct_letter


def mcq_options_small_set(correct: int, candidates: List[int]) -> Tuple[Dict[str, str], str]:
    """Pick 5 options (including correct) from a small candidate set (all ints)."""
    labels = ["A", "B", "C", "D", "E"]
    pool = set(candidates)
    pool.add(correct)
    chosen = set([correct])
    while len(chosen) < 5:
        chosen.add(random.choice(list(pool)))
    opts = list(chosen)
    random.shuffle(opts)
    correct_letter = labels[opts.index(correct)]
    return {labels[i]: i2s(opts[i]) for i in range(5)}, correct_letter


# ---------------- Symmetry counts ----------------
def symmetry_count(shape_name: str) -> Optional[int]:
    """
    Returns the integer number of symmetry lines for the given shape.
    If None → we won't ask symmetry for that shape.
    """
    mapping = {
        "square": 4,
        "rectangle": 2,
        "equilateral_triangle": 3,
        "isosceles_triangle": 1,
        "scalene_triangle": 0,
        "trapezium": 1,              # isosceles trapezium
        "parallelogram": 0,          # generic parallelogram has no symmetry lines
        "circle": None,              # infinite; skip symmetry questions to keep integers only
        "regular_hexagon": 6,
        "regular_pentagon": 5,
    }
    return mapping.get(shape_name, None)


# ---------------- Shape generators ----------------
# Each returns: (question_text, options_dict, correct_letter)
# Shapes must draw themselves and appropriate dimension lines.
# Missing dimension: label "?" (no units) on that dimension.

def gen_square(ax, rng, qtype):
    s = random.randint(*rng)
    draw_rect(ax, 0, 0, s, s)
    # Dimensions: top and left, offset outside the shape
    draw_dimension(ax, 0, s, s, s, f"{s} cm")             # top
    draw_dimension(ax, 0, 0, 0, s, f"{s} cm")             # left
    set_tidy_limits(ax, 0, 0, s, s)

    if qtype == "area":
        correct = s * s
        qtext = "What is the area of the given shape?"
        opts, letter = mcq_options_int(correct)
    elif qtype == "perimeter":
        correct = 4 * s
        qtext = "What is the perimeter of the given shape?"
        opts, letter = mcq_options_int(correct)
    elif qtype == "missing":
        # Hide side, give area
        draw_dimension(ax, 0, s, s, s, "?")               # replace top with '?'
        qtext = f"The area is {s*s} cm\u00b2. Find the side length (in cm)."
        correct = s
        opts, letter = mcq_options_int(correct)
    else:  # symmetry
        correct = 4
        qtext = "How many lines of symmetry does this shape contain?"
        opts, letter = mcq_options_small_set(correct, [0, 1, 2, 3, 4, 6])
    return qtext, opts, letter


def gen_rectangle(ax, rng, qtype):
    w = random.randint(*rng)
    h = random.randint(*rng)
    if w == h:
        w += 1  # avoid square case
    draw_rect(ax, 0, 0, w, h)
    draw_dimension(ax, 0, h, w, h, f"{w} cm")
    draw_dimension(ax, 0, 0, 0, h, f"{h} cm")
    set_tidy_limits(ax, 0, 0, w, h)

    if qtype == "area":
        correct = w * h
        qtext = "What is the area of the given shape?"
        opts, letter = mcq_options_int(correct)
    elif qtype == "perimeter":
        correct = 2 * (w + h)
        qtext = "What is the perimeter of the given shape?"
        opts, letter = mcq_options_int(correct)
    elif qtype == "missing":
        # Hide width; give area
        area = w * h
        draw_dimension(ax, 0, h, w, h, "?")
        qtext = f"The area is {area} cm\u00b2. Find the width (in cm)."
        correct = w
        opts, letter = mcq_options_int(correct)
    else:  # symmetry
        correct = 2
        qtext = "How many lines of symmetry does this shape contain?"
        opts, letter = mcq_options_small_set(correct, [0, 1, 2, 3, 4])
    return qtext, opts, letter


def gen_equilateral_triangle(ax, rng, qtype):
    s = random.randint(*rng)
    # Draw equilateral triangle with base on x-axis
    h = (math.sqrt(3) / 2.0) * s
    pts = [(0, 0), (s, 0), (s / 2.0, h)]
    draw_poly(ax, pts)
    # label base only (clean)
    draw_dimension(ax, 0, -0.2, s, -0.2, f"{s} cm")  # place just below base
    set_tidy_limits(ax, 0, 0, s, h)

    if qtype == "area":
        correct = clamp_int((math.sqrt(3) / 4.0) * s * s)
        qtext = "What is the area of the given shape?"
        opts, letter = mcq_options_int(correct)
    elif qtype == "perimeter":
        correct = 3 * s
        qtext = "What is the perimeter of the given shape?"
        opts, letter = mcq_options_int(correct)
    elif qtype == "missing":
        # Use area to ask for side; put '?' on base
        area = clamp_int((math.sqrt(3) / 4.0) * s * s)
        draw_dimension(ax, 0, -0.2, s, -0.2, "?")
        qtext = f"The area is {area} cm\u00b2. Find the side length (in cm)."
        correct = s
        opts, letter = mcq_options_int(correct)
    else:  # symmetry
        correct = 3
        qtext = "How many lines of symmetry does this shape contain?"
        opts, letter = mcq_options_small_set(correct, [0, 1, 2, 3, 6])
    return qtext, opts, letter


def gen_isosceles_triangle(ax, rng, qtype):
    base = random.randint(*rng)
    height = random.randint(*rng)
    # Coordinates: base along x-axis, apex centered
    pts = [(0, 0), (base, 0), (base / 2.0, height)]
    draw_poly(ax, pts)
    draw_dimension(ax, 0, -0.2, base, -0.2, f"{base} cm")  # base below
    draw_dimension(ax, base/2.0, 0, base/2.0, height, f"{height} cm")  # height
    set_tidy_limits(ax, 0, 0, base, height)

    if qtype == "area":
        correct = clamp_int(0.5 * base * height)
        qtext = "What is the area of the given shape?"
        opts, letter = mcq_options_int(correct)
    elif qtype == "perimeter":
        side = math.hypot(base / 2.0, height)
        correct = clamp_int(2 * side + base)
        qtext = "What is the perimeter of the given shape?"
        opts, letter = mcq_options_int(correct)
    elif qtype == "missing":
        # Hide height; give area
        area = clamp_int(0.5 * base * height)
        draw_dimension(ax, base/2.0, 0, base/2.0, height, "?")
        qtext = f"The area is {area} cm\u00b2. Find the height (in cm)."
        correct = height
        opts, letter = mcq_options_int(correct)
    else:  # symmetry
        correct = 1
        qtext = "How many lines of symmetry does this shape contain?"
        opts, letter = mcq_options_small_set(correct, [0, 1, 2, 3])
    return qtext, opts, letter


def gen_scalene_triangle(ax, rng, qtype):
    # Pick 3 sides satisfying triangle inequality
    a = random.randint(*rng)
    b = random.randint(*rng)
    c = random.randint(*rng)
    # Ensure triangle inequality
    def valid(a, b, c):
        return a + b > c and a + c > b and b + c > a
    attempts = 0
    while not valid(a, b, c) and attempts < 100:
        a = random.randint(*rng)
        b = random.randint(*rng)
        c = random.randint(*rng)
        attempts += 1

    # Place base a on x-axis, compute third point P by side lengths b (from x=0) and c (from x=a)
    # Using law of cosines to find x,y
    # x = (b^2 + a^2 - c^2)/(2a), y = sqrt(b^2 - x^2)
    x = (b*b + a*a - c*c) / (2.0 * a)
    y2 = b*b - x*x
    if y2 < 1e-9:
        y = 0.0
    else:
        y = math.sqrt(y2)

    pts = [(0, 0), (a, 0), (x, y)]
    draw_poly(ax, pts)
    # Label the three sides (near midpoints, slightly offset)
    draw_dimension(ax, 0, -0.2, a, -0.2, f"{a} cm")             # base
    draw_dimension(ax, 0, 0, x, y, f"{b} cm")
    draw_dimension(ax, a, 0, x, y, f"{c} cm")
    set_tidy_limits(ax, min(0, x), 0, max(a, x), max(0, y))

    if qtype == "area":
        # Heron's formula; round to integer
        s = 0.5 * (a + b + c)
        area = math.sqrt(max(s * (s - a) * (s - b) * (s - c), 0.0))
        correct = clamp_int(area)
        qtext = "What is the area of the given shape?"
        opts, letter = mcq_options_int(correct)
    elif qtype == "perimeter":
        correct = a + b + c
        qtext = "What is the perimeter of the given shape?"
        opts, letter = mcq_options_int(correct)
    elif qtype == "missing":
        # Ask for one side from perimeter: hide side 'a'
        draw_dimension(ax, 0, -0.2, a, -0.2, "?")
        total = a + b + c
        qtext = f"The perimeter is {total} cm. Find the missing side (in cm)."
        correct = a
        opts, letter = mcq_options_int(correct)
    else:  # symmetry
        correct = 0
        qtext = "How many lines of symmetry does this shape contain?"
        opts, letter = mcq_options_small_set(correct, [0, 1, 2, 3])
    return qtext, opts, letter


def gen_trapezium(ax, rng, qtype):
    # Isosceles trapezium
    top = random.randint(*rng)
    bottom = random.randint(max(top + 2, rng[0]+2), rng[1] + max(0, top - rng[0]))  # ensure bottom > top
    # Keep bottom within a sane range
    bottom = min(bottom, max(top + 2, rng[1]))
    h = random.randint(*rng)
    dx = (bottom - top) / 2.0
    pts = [(0, 0), (bottom, 0), (bottom - dx, h), (dx, h)]
    draw_poly(ax, pts)
    draw_dimension(ax, 0, -0.2, bottom, -0.2, f"{bottom} cm")
    draw_dimension(ax, dx, h + 0.2, bottom - dx, h + 0.2, f"{top} cm")
    draw_dimension(ax, -0.2, 0, -0.2, h, f"{h} cm")
    set_tidy_limits(ax, 0, 0, bottom, h)

    if qtype == "area":
        correct = clamp_int((top + bottom) * h / 2.0)
        qtext = "What is the area of the given shape?"
        opts, letter = mcq_options_int(correct)
    elif qtype == "perimeter":
        leg = math.hypot(dx, h)
        correct = clamp_int(top + bottom + 2 * leg)
        qtext = "What is the perimeter of the given shape?"
        opts, letter = mcq_options_int(correct)
    elif qtype == "missing":
        # Hide height; ask for height from area
        area = clamp_int((top + bottom) * h / 2.0)
        draw_dimension(ax, -0.2, 0, -0.2, h, "?")
        qtext = f"The area is {area} cm\u00b2. Find the height (in cm)."
        correct = h
        opts, letter = mcq_options_int(correct)
    else:  # symmetry (isosceles)
        correct = 1
        qtext = "How many lines of symmetry does this shape contain?"
        opts, letter = mcq_options_small_set(correct, [0, 1, 2, 3])
    return qtext, opts, letter


def gen_parallelogram(ax, rng, qtype):
    b = random.randint(*rng)
    h = random.randint(*rng)
    slant = random.randint(1, max(2, min(10, b//2)))
    pts = [(0, 0), (b, 0), (b + slant, h), (slant, h)]
    draw_poly(ax, pts)
    draw_dimension(ax, 0, -0.2, b, -0.2, f"{b} cm")
    draw_dimension(ax, -0.2 + slant, 0, -0.2 + slant, h, f"{h} cm")
    set_tidy_limits(ax, 0, 0, b + slant, h)

    if qtype == "area":
        correct = b * h
        qtext = "What is the area of the given shape?"
        opts, letter = mcq_options_int(correct)
    elif qtype == "perimeter":
        side = math.hypot(slant, h)
        correct = clamp_int(2 * (b + side))
        qtext = "What is the perimeter of the given shape?"
        opts, letter = mcq_options_int(correct)
    elif qtype == "missing":
        # Hide base; ask for base from area
        area = b * h
        draw_dimension(ax, 0, -0.2, b, -0.2, "?")
        qtext = f"The area is {area} cm\u00b2. Find the base (in cm)."
        correct = b
        opts, letter = mcq_options_int(correct)
    else:  # symmetry
        correct = 0
        qtext = "How many lines of symmetry does this shape contain?"
        opts, letter = mcq_options_small_set(correct, [0, 1, 2, 3])
    return qtext, opts, letter


def gen_circle(ax, rng, qtype):
    r = random.randint(*rng)
    draw_circle(ax, 0, 0, r)
    # Draw diameter line and label
    draw_line(ax, -r, 0, r, 0)
    if qtype == "missing":
        draw_dimension(ax, -r, -0.3, r, -0.3, "?")
    else:
        draw_dimension(ax, -r, -0.3, r, -0.3, f"{2*r} cm")
    set_tidy_limits(ax, -r - 1, -r - 1, r + 1, r + 1)

    if qtype == "area":
        correct = clamp_int(math.pi * r * r)
        qtext = "What is the area of the given shape?"
        opts, letter = mcq_options_int(correct)
    elif qtype == "perimeter":
        correct = clamp_int(2 * math.pi * r)
        qtext = "What is the circumference of the given shape?"
        opts, letter = mcq_options_int(correct)
    elif qtype == "missing":
        # Given circumference, find radius
        C = clamp_int(2 * math.pi * r)
        qtext = f"The circumference is {C} cm. Find the radius (in cm)."
        correct = r
        opts, letter = mcq_options_int(correct)
    else:
        # Skip symmetry for circle (infinite). Fall back to perimeter.
        correct = clamp_int(2 * math.pi * r)
        qtext = "What is the circumference of the given shape?"
        opts, letter = mcq_options_int(correct)
    return qtext, opts, letter


def gen_regular_ngon(ax, rng, qtype, n: int, name: str):
    s = random.randint(*rng)
    # Draw a regular n-gon centered roughly, with one side horizontal for clarity
    # Radius for circumcircle; place vertices
    R = s / (2 * math.sin(math.pi / n))
    cx, cy = (0, 0)
    verts = []
    # rotate so that one side is horizontal at bottom
    theta0 = -math.pi / 2 - math.pi / n
    for k in range(n):
        angle = theta0 + 2 * math.pi * k / n
        x = cx + R * math.cos(angle)
        y = cy + R * math.sin(angle)
        verts.append((x, y))
    draw_poly(ax, verts)
    # Label one side length (the bottom-most side approximately)
    # Find the lowest y edge
    low_idx = min(range(n), key=lambda i: (verts[i][1] + verts[(i+1) % n][1]) / 2.0)
    x1, y1 = verts[low_idx]
    x2, y2 = verts[(low_idx + 1) % n]
    draw_dimension(ax, x1, y1 - 0.2, x2, y2 - 0.2, f"{s} cm")
    xs = [p[0] for p in verts]
    ys = [p[1] for p in verts]
    set_tidy_limits(ax, min(xs), min(ys), max(xs), max(ys))

    if qtype == "area":
        # Area of regular n-gon: A = (n * s^2) / (4 * tan(pi/n))
        area = (n * s * s) / (4.0 * math.tan(math.pi / n))
        correct = clamp_int(area)
        qtext = "What is the area of the given shape?"
        opts, letter = mcq_options_int(correct)
    elif qtype == "perimeter":
        correct = n * s
        qtext = "What is the perimeter of the given shape?"
        opts, letter = mcq_options_int(correct)
    elif qtype == "missing":
        # Ask for side from perimeter: hide the labeled side
        P = n * s
        draw_dimension(ax, x1, y1 - 0.2, x2, y2 - 0.2, "?")
        qtext = f"The perimeter is {P} cm. Find the side length (in cm)."
        correct = s
        opts, letter = mcq_options_int(correct)
    else:  # symmetry
        sym = n
        qtext = "How many lines of symmetry does this shape contain?"
        opts, letter = mcq_options_small_set(sym, list(range(0, n+1)))
        correct = sym  # for return consistency
    return qtext, opts, letter


# ------------- Main question generator -------------
SHAPES = [
    "square", "rectangle", "equilateral_triangle", "isosceles_triangle",
    "scalene_triangle", "trapezium", "parallelogram", "circle",
    "regular_hexagon", "regular_pentagon"
]

Q_TYPES = ["area", "perimeter", "missing", "symmetry"]  # 'perimeter' also means circumference for circle


def gen_one(ax, shape: str, diff: str) -> Tuple[str, Dict[str, str], str]:
    rng = DIFF_RANGES[diff]
    # For circle, don't generate symmetry (to keep integer answers only)
    qtype = random.choice(Q_TYPES if shape != "circle" else ["area", "perimeter", "missing"])

    if shape == "square":
        return gen_square(ax, rng, qtype)
    if shape == "rectangle":
        return gen_rectangle(ax, rng, qtype)
    if shape == "equilateral_triangle":
        return gen_equilateral_triangle(ax, rng, qtype)
    if shape == "isosceles_triangle":
        return gen_isosceles_triangle(ax, rng, qtype)
    if shape == "scalene_triangle":
        return gen_scalene_triangle(ax, rng, qtype)
    if shape == "trapezium":
        return gen_trapezium(ax, rng, qtype)
    if shape == "parallelogram":
        return gen_parallelogram(ax, rng, qtype)
    if shape == "circle":
        return gen_circle(ax, rng, qtype)
    if shape == "regular_hexagon":
        return gen_regular_ngon(ax, rng, qtype, 6, "regular_hexagon")
    if shape == "regular_pentagon":
        return gen_regular_ngon(ax, rng, qtype, 5, "regular_pentagon")
    # Fallback (shouldn't happen)
    return "What is the area of the given shape?", *mcq_options_int(1)


# ---------------- Main loop ----------------
def main():
    ensure_dirs()
    out: List[Dict[str, Any]] = []

    for i in range(1, questionVolume + 1):
        diff = random.choice(DIFF_LIST)
        shape = random.choice(SHAPES)

        fig, ax = plt.subplots(figsize=FIGSIZE)
        ax.set_aspect("equal")
        ax.axis("off")

        qtext, options, correct_letter = gen_one(ax, shape, diff)

        # Save image
        img_name = f"Q{i}.png"
        img_path = os.path.join(BASE_IMG_DIR, diff, img_name)
        plt.savefig(img_path, dpi=DPI, bbox_inches="tight", pad_inches=0.25)
        plt.close(fig)

        # Build JSON record
        record = {
            "question": qtext,
            "correct_answer": options[correct_letter],   # value (string) of correct option
            "options": options,                          # dict {"A": "12", ...}
            "difficulty_level": diff,
            "img_path": img_path
        }
        out.append(record)

        if i % 100 == 0:
            print(f"Generated {i}/{questionVolume}")

    with open(OUT_JSON, "w") as f:
        json.dump(out, f, indent=2)

    print("✅ Done.")
    print(f"Images saved under ./{BASE_IMG_DIR}/[easy|medium|difficult]/")
    print(f"Questions JSON saved to ./{OUT_JSON}")


if __name__ == "__main__":
    main()
