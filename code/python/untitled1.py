#!/usr/bin/env python3
"""
Fast Geometry MCQ Generator (10 shapes, 3 difficulty levels)

Shapes:
- square, rectangle, equilateral_triangle, isosceles_triangle, scalene_triangle,
  trapezium (isosceles), parallelogram, circle, regular_hexagon, regular_pentagon

Difficulties & integer ranges (cm):
- easy: 1–10
- medium: 11–50
- difficult: 51–100

Question types (random per question):
- area, perimeter/circumference, missing dimension (side/width/height/radius/diameter),
  symmetry (integer answers only; circle excluded from symmetry)

Output:
- Images under images/[easy|medium|difficult]/Q#.png
- questions.json with keys: {question, correct_answer, options, difficulty_level, img_path}

Notes:
- All answer options are integers in STRING format, e.g., "42".
- Dimension labels use a white background box (foreground) and are offset so they never touch edges.
- When a dimension is unknown, the dimension line is drawn and labeled "?" (NO units).
- Non-GUI backend, threaded generation → fast for large volumes (e.g., 1000).
"""

import os
import json
import math
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Any, Optional

import matplotlib
matplotlib.use("Agg")  # headless, fast
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle

# ----------------- CONFIG -----------------
questionVolume = 1000
OUT_JSON = "questions.json"
BASE_IMG_DIR = "images"

DIFF_RANGES = {
    "easy": (1, 10),
    "medium": (11, 50),
    "difficult": (51, 100),
}
DIFF_LEVELS = list(DIFF_RANGES.keys())

SHAPES = [
    "square", "rectangle", "equilateral_triangle", "isosceles_triangle",
    "scalene_triangle", "trapezium", "parallelogram", "circle",
    "regular_hexagon", "regular_pentagon",
]

Q_TYPES = ["area", "perimeter", "missing", "symmetry"]  # circle won't use 'symmetry'

# Figure / style (balanced for speed + clarity)
FIGSIZE = (2.5, 2.5)
DPI = 150
PAD = 0.8
LINE_W = 1.6
FS_DIM = 8

# Use a robust font to prevent '?' glyphs
matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.linewidth": 0.8,
})


# ----------------- UTILITIES -----------------
def ensure_dirs():
    for d in DIFF_LEVELS:
        os.makedirs(os.path.join(BASE_IMG_DIR, d), exist_ok=True)


def i2s(n: int) -> str:
    return str(int(n))


def clamp_int(x: float) -> int:
    return int(round(x))


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
    # Foreground text in a white box so lines behind never interfere
    ax.text(
        x, y, text, ha="center", va="center",
        fontsize=FS_DIM, rotation=rot,
        bbox=dict(facecolor="white", edgecolor="none", pad=1.0),
        zorder=10
    )


def draw_dimension(ax, x1, y1, x2, y2, label: Optional[str], offset=0.28):
    """
    Draws a dimension line parallel to segment (x1,y1)-(x2,y2), offset from the shape
    so it never touches edges. No T-caps.

    label:
      - "12 cm" → draw line & label with units
      - "?"     → draw line & label with "?" (no units)
      - None    → draw nothing (used if we want to fully omit a dimension)
    """
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    if L < 1e-9 or label is None:
        return
    # perpendicular unit for offset
    nx, ny = -dy / L, dx / L
    sx1, sy1 = x1 + nx * offset, y1 + ny * offset
    sx2, sy2 = x2 + nx * offset, y2 + ny * offset
    draw_line(ax, sx1, sy1, sx2, sy2, zorder=2)
    mx, my = (sx1 + sx2) / 2.0, (sy1 + sy2) / 2.0
    angle = math.degrees(math.atan2(dy, dx))
    # Normalize rotation for readability on near-horizontal lines
    if abs(abs(angle) - 180) < 1e-3 or abs(angle) < 1e-3:
        angle = 0
    label_text(ax, mx, my, label, rot=angle)


def mcq_options_int(correct_value: int) -> Tuple[Dict[str, str], str]:
    """
    Create A–E integer options (strings) around the integer 'correct_value'.
    Ensures unique, positive integers. Returns (options_dict, correct_letter).
    """
    correct = int(correct_value)
    labels = ["A", "B", "C", "D", "E"]
    cand = set([correct])
    spread = max(6, int(abs(correct) * 0.2))
    while len(cand) < 5:
        delta = random.randint(1, spread)
        val = correct + random.choice([-delta, delta])
        if val > 0:
            cand.add(val)
    opts = list(cand)
    random.shuffle(opts)
    correct_letter = labels[opts.index(correct)]
    return {labels[i]: i2s(opts[i]) for i in range(5)}, correct_letter


def mcq_options_small(correct: int, pool: List[int]) -> Tuple[Dict[str, str], str]:
    labels = ["A", "B", "C", "D", "E"]
    s = set(pool)
    s.add(correct)
    chosen = set([correct])
    while len(chosen) < 5:
        chosen.add(random.choice(list(s)))
    opts = list(chosen)
    random.shuffle(opts)
    correct_letter = labels[opts.index(correct)]
    return {labels[i]: i2s(opts[i]) for i in range(5)}, correct_letter


# ----------------- SHAPES -----------------
def gen_square(ax, rng, qtype):
    s = random.randint(*rng)
    draw_rect(ax, 0, 0, s, s)
    draw_dimension(ax, 0, s, s, s, f"{s} cm")      # top
    draw_dimension(ax, 0, 0, 0, s, f"{s} cm")      # left
    set_tidy_limits(ax, 0, 0, s, s)

    if qtype == "area":
        correct = s * s
        qtext = "What is the area of the given shape?"
        options, letter = mcq_options_int(correct)
    elif qtype == "perimeter":
        correct = 4 * s
        qtext = "What is the perimeter of the given shape?"
        options, letter = mcq_options_int(correct)
    elif qtype == "missing":
        # Replace top dimension with '?'
        draw_dimension(ax, 0, s, s, s, "?")
        qtext = f"The area is {s*s} cm^2. Find the side length (in cm)."
        correct = s
        options, letter = mcq_options_int(correct)
    else:  # symmetry
        correct = 4
        qtext = "How many lines of symmetry does this shape contain?"
        options, letter = mcq_options_small(correct, [0, 1, 2, 3, 4, 6])
    return qtext, options, letter


def gen_rectangle(ax, rng, qtype):
    w = random.randint(*rng)
    h = random.randint(*rng)
    if w == h:
        w += 1
    draw_rect(ax, 0, 0, w, h)
    draw_dimension(ax, 0, h, w, h, f"{w} cm")
    draw_dimension(ax, 0, 0, 0, h, f"{h} cm")
    set_tidy_limits(ax, 0, 0, w, h)

    if qtype == "area":
        correct = w * h
        qtext = "What is the area of the given shape?"
        options, letter = mcq_options_int(correct)
    elif qtype == "perimeter":
        correct = 2 * (w + h)
        qtext = "What is the perimeter of the given shape?"
        options, letter = mcq_options_int(correct)
    elif qtype == "missing":
        draw_dimension(ax, 0, h, w, h, "?")
        qtext = f"The area is {w*h} cm^2. Find the width (in cm)."
        correct = w
        options, letter = mcq_options_int(correct)
    else:
        correct = 2
        qtext = "How many lines of symmetry does this shape contain?"
        options, letter = mcq_options_small(correct, [0, 1, 2, 3, 4])
    return qtext, options, letter


def gen_equilateral_triangle(ax, rng, qtype):
    s = random.randint(*rng)
    h = (math.sqrt(3) / 2.0) * s
    pts = [(0, 0), (s, 0), (s/2.0, h)]
    draw_poly(ax, pts)
    draw_dimension(ax, 0, -0.25, s, -0.25, f"{s} cm")
    set_tidy_limits(ax, 0, 0, s, h)

    if qtype == "area":
        correct = clamp_int((math.sqrt(3) / 4.0) * s * s)
        qtext = "What is the area of the given shape?"
        options, letter = mcq_options_int(correct)
    elif qtype == "perimeter":
        correct = 3 * s
        qtext = "What is the perimeter of the given shape?"
        options, letter = mcq_options_int(correct)
    elif qtype == "missing":
        area = clamp_int((math.sqrt(3) / 4.0) * s * s)
        draw_dimension(ax, 0, -0.25, s, -0.25, "?")
        qtext = f"The area is {area} cm^2. Find the side length (in cm)."
        correct = s
        options, letter = mcq_options_int(correct)
    else:
        correct = 3
        qtext = "How many lines of symmetry does this shape contain?"
        options, letter = mcq_options_small(correct, [0, 1, 2, 3, 6])
    return qtext, options, letter


def gen_isosceles_triangle(ax, rng, qtype):
    base = random.randint(*rng)
    height = random.randint(*rng)
    pts = [(0, 0), (base, 0), (base/2.0, height)]
    draw_poly(ax, pts)
    draw_dimension(ax, 0, -0.25, base, -0.25, f"{base} cm")
    draw_dimension(ax, base/2.0, 0, base/2.0, height, f"{height} cm")
    set_tidy_limits(ax, 0, 0, base, height)

    if qtype == "area":
        correct = clamp_int(0.5 * base * height)
        qtext = "What is the area of the given shape?"
        options, letter = mcq_options_int(correct)
    elif qtype == "perimeter":
        side = math.hypot(base/2.0, height)
        correct = clamp_int(base + 2 * side)
        qtext = "What is the perimeter of the given shape?"
        options, letter = mcq_options_int(correct)
    elif qtype == "missing":
        area = clamp_int(0.5 * base * height)
        # Hide the height
        draw_dimension(ax, base/2.0, 0, base/2.0, height, "?")
        qtext = f"The area is {area} cm^2. Find the height (in cm)."
        correct = height
        options, letter = mcq_options_int(correct)
    else:
        correct = 1
        qtext = "How many lines of symmetry does this shape contain?"
        options, letter = mcq_options_small(correct, [0, 1, 2, 3])
    return qtext, options, letter


def gen_scalene_triangle(ax, rng, qtype):
    # pick sides satisfying triangle inequality
    def valid(a, b, c):
        return a + b > c and a + c > b and b + c > a
    tries = 0
    a = b = c = 0
    while tries < 100:
        a = random.randint(*rng)  # base
        b = random.randint(*rng)
        c = random.randint(*rng)
        if valid(a, b, c) and len({a, b, c}) == 3:
            break
        tries += 1
    # Coordinates using law of cosines
    x = (b*b + a*a - c*c) / (2.0 * a)
    y2 = b*b - x*x
    y = math.sqrt(max(y2, 0.0))
    pts = [(0, 0), (a, 0), (x, y)]
    draw_poly(ax, pts)
    draw_dimension(ax, 0, -0.25, a, -0.25, f"{a} cm")
    draw_dimension(ax, 0, 0, x, y, f"{b} cm")
    draw_dimension(ax, a, 0, x, y, f"{c} cm")
    set_tidy_limits(ax, min(0, x), 0, max(a, x), max(0, y))

    if qtype == "area":
        s = 0.5 * (a + b + c)
        area = math.sqrt(max(s * (s - a) * (s - b) * (s - c), 0.0))
        correct = clamp_int(area)
        qtext = "What is the area of the given shape?"
        options, letter = mcq_options_int(correct)
    elif qtype == "perimeter":
        correct = a + b + c
        qtext = "What is the perimeter of the given shape?"
        options, letter = mcq_options_int(correct)
    elif qtype == "missing":
        # Hide the base; give perimeter
        P = a + b + c
        draw_dimension(ax, 0, -0.25, a, -0.25, "?")
        qtext = f"The perimeter is {P} cm. Find the missing side (in cm)."
        correct = a
        options, letter = mcq_options_int(correct)
    else:
        correct = 0
        qtext = "How many lines of symmetry does this shape contain?"
        options, letter = mcq_options_small(correct, [0, 1, 2, 3])
    return qtext, options, letter


def gen_trapezium(ax, rng, qtype):
    # isosceles trapezium
    top = random.randint(*rng)
    bottom = random.randint(max(top + 2, rng[0] + 2), max(top + 2, rng[1]))
    h = random.randint(*rng)
    dx = (bottom - top) / 2.0
    pts = [(0, 0), (bottom, 0), (bottom - dx, h), (dx, h)]
    draw_poly(ax, pts)
    draw_dimension(ax, 0, -0.25, bottom, -0.25, f"{bottom} cm")
    draw_dimension(ax, dx, h + 0.25, bottom - dx, h + 0.25, f"{top} cm")
    draw_dimension(ax, -0.25, 0, -0.25, h, f"{h} cm")
    set_tidy_limits(ax, 0, 0, bottom, h)

    if qtype == "area":
        correct = clamp_int((top + bottom) * h / 2.0)
        qtext = "What is the area of the given shape?"
        options, letter = mcq_options_int(correct)
    elif qtype == "perimeter":
        leg = math.hypot(dx, h)
        correct = clamp_int(top + bottom + 2 * leg)
        qtext = "What is the perimeter of the given shape?"
        options, letter = mcq_options_int(correct)
    elif qtype == "missing":
        area = clamp_int((top + bottom) * h / 2.0)
        draw_dimension(ax, -0.25, 0, -0.25, h, "?")
        qtext = f"The area is {area} cm^2. Find the height (in cm)."
        correct = h
        options, letter = mcq_options_int(correct)
    else:
        correct = 1  # isosceles trapezium
        qtext = "How many lines of symmetry does this shape contain?"
        options, letter = mcq_options_small(correct, [0, 1, 2, 3])
    return qtext, options, letter


def gen_parallelogram(ax, rng, qtype):
    b = random.randint(*rng)
    h = random.randint(*rng)
    slant = random.randint(1, max(2, min(10, b // 2)))
    pts = [(0, 0), (b, 0), (b + slant, h), (slant, h)]
    draw_poly(ax, pts)
    draw_dimension(ax, 0, -0.25, b, -0.25, f"{b} cm")
    draw_dimension(ax, -0.25 + slant, 0, -0.25 + slant, h, f"{h} cm")
    set_tidy_limits(ax, 0, 0, b + slant, h)

    if qtype == "area":
        correct = b * h
        qtext = "What is the area of the given shape?"
        options, letter = mcq_options_int(correct)
    elif qtype == "perimeter":
        side = math.hypot(slant, h)
        correct = clamp_int(2 * (b + side))
        qtext = "What is the perimeter of the given shape?"
        options, letter = mcq_options_int(correct)
    elif qtype == "missing":
        draw_dimension(ax, 0, -0.25, b, -0.25, "?")
        qtext = f"The area is {b*h} cm^2. Find the base (in cm)."
        correct = b
        options, letter = mcq_options_int(correct)
    else:
        correct = 0
        qtext = "How many lines of symmetry does this shape contain?"
        options, letter = mcq_options_small(correct, [0, 1, 2, 3])
    return qtext, options, letter


def gen_circle(ax, rng, qtype):
    r = random.randint(*rng)
    draw_circle(ax, 0, 0, r)
    # draw diameter line
    draw_line(ax, -r, 0, r, 0)
    if qtype == "missing":
        draw_dimension(ax, -r, -0.3, r, -0.3, "?")
    else:
        draw_dimension(ax, -r, -0.3, r, -0.3, f"{2*r} cm")
    set_tidy_limits(ax, -r - 1, -r - 1, r + 1, r + 1)

    if qtype == "area":
        correct = clamp_int(math.pi * r * r)
        qtext = "What is the area of the given shape?"
        options, letter = mcq_options_int(correct)
    elif qtype == "perimeter":
        correct = clamp_int(2 * math.pi * r)
        qtext = "What is the circumference of the given shape?"
        options, letter = mcq_options_int(correct)
    elif qtype == "missing":
        C = clamp_int(2 * math.pi * r)
        qtext = f"The circumference is {C} cm. Find the radius (in cm)."
        correct = r
        options, letter = mcq_options_int(correct)
    else:
        # skip symmetry for circle → ask perimeter instead
        correct = clamp_int(2 * math.pi * r)
        qtext = "What is the circumference of the given shape?"
        options, letter = mcq_options_int(correct)
    return qtext, options, letter


def gen_regular_ngon(ax, rng, qtype, n: int):
    s = random.randint(*rng)
    R = s / (2.0 * math.sin(math.pi / n))
    cx = cy = 0.0
    verts = []
    theta0 = -math.pi / 2 - math.pi / n  # one side roughly horizontal near bottom
    for k in range(n):
        ang = theta0 + 2 * math.pi * k / n
        verts.append((cx + R * math.cos(ang), cy + R * math.sin(ang)))
    draw_poly(ax, verts)

    # find lowest edge (for labeling side length)
    idx = min(range(n), key=lambda i: (verts[i][1] + verts[(i+1) % n][1]) / 2.0)
    x1, y1 = verts[idx]
    x2, y2 = verts[(idx + 1) % n]
    draw_dimension(ax, x1, y1 - 0.25, x2, y2 - 0.25, f"{s} cm")

    xs = [p[0] for p in verts]
    ys = [p[1] for p in verts]
    set_tidy_limits(ax, min(xs), min(ys), max(xs), max(ys))

    if qtype == "area":
        area = (n * s * s) / (4.0 * math.tan(math.pi / n))
        correct = clamp_int(area)
        qtext = "What is the area of the given shape?"
        options, letter = mcq_options_int(correct)
    elif qtype == "perimeter":
        correct = n * s
        qtext = "What is the perimeter of the given shape?"
        options, letter = mcq_options_int(correct)
    elif qtype == "missing":
        P = n * s
        draw_dimension(ax, x1, y1 - 0.25, x2, y2 - 0.25, "?")
        qtext = f"The perimeter is {P} cm. Find the side length (in cm)."
        correct = s
        options, letter = mcq_options_int(correct)
    else:
        correct = n
        qtext = "How many lines of symmetry does this shape contain?"
        options, letter = mcq_options_small(correct, list(range(0, max(8, n+1))))
    return qtext, options, letter


# ----------------- DISPATCH -----------------
def gen_one(ax, shape: str, diff: str) -> Tuple[str, Dict[str, str], str]:
    rng = DIFF_RANGES[diff]
    qtype = random.choice(Q_TYPES if shape != "circle" else ["area", "perimeter", "missing"])

    if shape == "square":
        return gen_square(ax, rng, qtype)
    elif shape == "rectangle":
        return gen_rectangle(ax, rng, qtype)
    elif shape == "equilateral_triangle":
        return gen_equilateral_triangle(ax, rng, qtype)
    elif shape == "isosceles_triangle":
        return gen_isosceles_triangle(ax, rng, qtype)
    elif shape == "scalene_triangle":
        return gen_scalene_triangle(ax, rng, qtype)
    elif shape == "trapezium":
        return gen_trapezium(ax, rng, qtype)
    elif shape == "parallelogram":
        return gen_parallelogram(ax, rng, qtype)
    elif shape == "circle":
        return gen_circle(ax, rng, qtype)
    elif shape == "regular_hexagon":
        return gen_regular_ngon(ax, rng, qtype, 6)
    elif shape == "regular_pentagon":
        return gen_regular_ngon(ax, rng, qtype, 5)
    # Fallback
    return gen_square(ax, rng, "area")


# ----------------- PER-QUESTION WORKER -----------------
def build_one(idx: int) -> Dict[str, Any]:
    diff = random.choice(DIFF_LEVELS)
    shape = random.choice(SHAPES)

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.set_aspect("equal")
    ax.axis("off")

    qtext, options, correct_letter = gen_one(ax, shape, diff)

    img_name = f"Q{idx}.png"
    img_path = os.path.join(BASE_IMG_DIR, diff, img_name)
    fig.savefig(img_path, dpi=DPI, bbox_inches="tight", pad_inches=0.22)
    plt.close(fig)

    return {
        "question": qtext,
        "correct_answer": correct_letter,  # LETTER A–E
        "options": options,                # dict {"A": "12", ...}
        "difficulty_level": diff,
        "img_path": img_path
    }


# ----------------- MAIN -----------------
def main():
    ensure_dirs()
    out: List[Dict[str, Any]] = []

    # Threading: image encoding is I/O-bound, so threads help
    max_workers = max(4, (os.cpu_count() or 4))
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(build_one, i) for i in range(1, questionVolume + 1)]
        for f in as_completed(futures):
            out.append(f.result())

    # Keep deterministic order by img_path (Q#)
    out.sort(key=lambda r: r["img_path"])

    with open(OUT_JSON, "w") as f:
        json.dump(out, f, indent=2)

    print(f"✅ Generated {len(out)} questions.")
    print(f"📁 Images: ./{BASE_IMG_DIR}/(easy|medium|difficult)/Q#.png")
    print(f"📝 JSON  : ./{OUT_JSON}")


if __name__ == "__main__":
    main()
