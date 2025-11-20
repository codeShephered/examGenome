#!/usr/bin/env python3
"""
generate_1000_shapes.py
Single-file runnable script to generate 1000 black-and-white exam-style shape images
and a JSON file with question text, options A-E, correct answer, and image path.

Requires: matplotlib
pip install matplotlib
"""

import os
import math
import json
import random
from typing import Tuple, List, Dict, Any

import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Rectangle, Polygon, Circle

# ---------------- Config ----------------
NUM_QUESTIONS = 1000
IMG_DIR = "images"
JSON_PATH = "questions.json"
FIGSIZE = (4.5, 4.5)
DPI = 150

# Visual params
LINE_W = 1.6
'''FS_DIM = 9'''
FS_DIM = 6
PAD = 0.4


# Set clean readable font globally
mpl.rcParams['font.family'] = 'DejaVu Sans'

random.seed()  # set seed here for reproducibility if desired e.g. random.seed(42)


# ---------------- Utility drawing helpers ----------------
def ensure_dirs():
    os.makedirs(IMG_DIR, exist_ok=True)

def draw_line(ax, x1, y1, x2, y2, **kwargs):
    # sensible defaults; allow overrides via kwargs (incl. zorder)
    kwargs.setdefault("color", "black")
    kwargs.setdefault("linewidth", LINE_W)
    ax.plot([x1, x2], [y1, y2], **kwargs)


def draw_rect(ax, x, y, w, h, **kwargs):
    kwargs.setdefault("edgecolor", "black")
    kwargs.setdefault("linewidth", LINE_W)
    ax.add_patch(Rectangle((x, y), w, h, fill=False, **kwargs))


def draw_poly(ax, pts, **kwargs):
    kwargs.setdefault("edgecolor", "black")
    kwargs.setdefault("linewidth", LINE_W)
    ax.add_patch(Polygon(pts, closed=True, fill=False, **kwargs))


'''
def draw_line(ax, x1, y1, x2, y2):
    ax.plot([x1, x2], [y1, y2], color="black", linewidth=LINE_W)

def draw_rect(ax, x, y, w, h):
    ax.add_patch(Rectangle((x, y), w, h, fill=False, edgecolor="black", linewidth=LINE_W))


def draw_poly(ax, pts):
    ax.add_patch(Polygon(pts, closed=True, fill=False, edgecolor="black", linewidth=LINE_W))
    
def draw_dimension(ax, x1, y1, x2, y2, label_text, cap=0.20):
    """
    Draw a dimension line between (x1,y1) and (x2,y2) without inverted 'T' caps,
    keeping the dimension label always on top with a white background box.
    """
    # main line
    draw_line(ax, x1, y1, x2, y2, zorder=1)

    dx = x2 - x1
    dy = y2 - y1
    horizontal = abs(dy) < 1e-6
    vertical = abs(dx) < 1e-6

    txt = f"{int(round(label_text))} cm" if isinstance(label_text, (int, float)) else str(label_text)

    if horizontal:
        txt_y = y1 + cap + 0.08
        ax.text(
            (x1 + x2) / 2.0, txt_y, txt,
            ha="center", va="bottom", fontsize=FS_DIM,
            bbox=dict(facecolor="white", edgecolor="none", pad=1),
            zorder=10
        )
    elif vertical:
        txt_x = x1 + cap + 0.08
        ax.text(
            txt_x, (y1 + y2) / 2.0, txt,
            ha="left", va="center", rotation=90, fontsize=FS_DIM,
            bbox=dict(facecolor="white", edgecolor="none", pad=1),
            zorder=10
        )
    else:
        L = math.hypot(dx, dy)
        if L < 1e-6:
            return
        ax.text(
            (x1 + x2) / 2.0, (y1 + y2) / 2.0, txt,
            ha="center", va="bottom", fontsize=FS_DIM,
            bbox=dict(facecolor="white", edgecolor="none", pad=1),
            zorder=10
        )

def draw_dimension(ax, x1, y1, x2, y2, label_text, cap=0.20):
    """
    Draw a clean dimension line (no caps) and put the label in the foreground
    with a white background box so nothing shows through.
    """
    # draw the dimension line behind the label
    draw_line(ax, x1, y1, x2, y2, zorder=1)

    dx, dy = x2 - x1, y2 - y1
    horizontal = abs(dy) < 1e-6
    vertical   = abs(dx) < 1e-6

    txt = f"{int(round(label_text))} cm" if isinstance(label_text, (int, float)) else str(label_text)

    if horizontal:
        # position above the line
        txt_y = y1 + cap + 0.08
        ax.text(
            (x1 + x2) / 2.0, txt_y, txt,
            ha="center", va="bottom", fontsize=FS_DIM,
            bbox=dict(facecolor="white", edgecolor="none", pad=1.5),
            zorder=10
        )
    elif vertical:
        # position to the right of the line
        txt_x = x1 + cap + 0.08
        ax.text(
            txt_x, (y1 + y2) / 2.0, txt,
            ha="left", va="center", rotation=90, fontsize=FS_DIM,
            bbox=dict(facecolor="white", edgecolor="none", pad=1.5),
            zorder=10
        )
    else:
        # diagonal: center on the segment
        ax.text(
            (x1 + x2) / 2.0, (y1 + y2) / 2.0, txt,
            ha="center", va="bottom", fontsize=FS_DIM,
            bbox=dict(facecolor="white", edgecolor="none", pad=1.5),
            zorder=10
        )

'''
import math
import matplotlib as mpl

# Set clean readable font globally
mpl.rcParams['font.family'] = 'DejaVu Sans'


def draw_dimension(ax, x1, y1, x2, y2, label_text, cap=0.20):
    """
    Draw a dimension line between (x1, y1) and (x2, y2) with perpendicular 'T' caps and label.
    Always keeps text sharp and visible on top of lines.
    """
    # main line (low zorder so text will be on top)
    draw_line(ax, x1, y1, x2, y2)

    dx = x2 - x1
    dy = y2 - y1
    horizontal = abs(dy) < 1e-6
    vertical = abs(dx) < 1e-6

    # Format label
    txt = f"{int(round(label_text))} cm" if isinstance(label_text, (int)) else str(label_text)
    """label_txt = ''"""

    # Draw caps + place text
    if horizontal:
        draw_line(ax, x1, y1 - cap, x1, y1 + cap)
        draw_line(ax, x2, y2 - cap, x2, y2 + cap)
        txt_y = y1 + cap + 0.08
        ax.text(
            (x1 + x2) / 2.0, txt_y, txt,
            ha="center", va="bottom", fontsize=FS_DIM,
            bbox=dict(facecolor="white", edgecolor="none", pad=1.5),
            zorder=10
        )
    elif vertical:
        draw_line(ax, x1 - cap, y1, x1 + cap, y1)
        draw_line(ax, x2 - cap, y2, x2 + cap, y2)
        txt_x = x1 + cap + 0.08
        ax.text(
            txt_x, (y1 + y2) / 2.0, txt,
            ha="left", va="center", rotation=90, fontsize=FS_DIM,
            bbox=dict(facecolor="white", edgecolor="none", pad=1.5),
            zorder=10
        )
    else:
        # diagonal
        L = math.hypot(dx, dy)
        if L < 1e-6:
            return
        px, py = -dy / L, dx / L
        draw_line(ax, x1 - px * cap, y1 - py * cap, x1 + px * cap, y1 + py * cap)
        draw_line(ax, x2 - px * cap, y2 - py * cap, x2 + px * cap, y2 + py * cap)
        ax.text(
            (x1 + x2) / 2.0, (y1 + y2) / 2.0, txt,
            ha="center", va="bottom", fontsize=FS_DIM,
            bbox=dict(facecolor="white", edgecolor="none", pad=1.5),
            zorder=10
        )


def set_tidy_limits(ax, xmin, ymin, xmax, ymax):
    ax.set_aspect("equal")
    ax.set_xlim(xmin - PAD, xmax + PAD)
    ax.set_ylim(ymin - PAD, ymax + PAD)
    ax.axis("off")


# ---------------- MCQ generator (robust) ----------------
def generate_mcq_int(correct_value: float) -> Tuple[Dict[str, int], str]:
    """
    Produce 5 integer options A-E around the integer-rounded correct value.
    Returns (options_dict, correct_letter). Ensures uniqueness and no negatives.
    """
    correct = int(round(correct_value))
    # Choose delta span proportional to magnitude but ensure at least a minimum spread
    mag = max(1, abs(correct))
    # delta candidates up to approx 20% of mag or at least up to 8
    max_delta = max(8, int(math.ceil(mag * 0.2)))
    deltas = list(range(1, max_delta + 1))

    distractors = set()
    # fill until 4 unique distractors
    while len(distractors) < 4:
        d = random.choice(deltas)
        cand = correct + random.choice([-d, d])
        if cand == correct:
            continue
        if cand < 0:
            continue
        distractors.add(cand)

    options_list = list(distractors) + [correct]
    random.shuffle(options_list)
    labels = ["A", "B", "C", "D", "E"]
    correct_letter = labels[options_list.index(correct)]
    options_dict = {labels[i]: int(options_list[i]) for i in range(5)}
    return options_dict, correct_letter


def generate_mcq_small_candidates(correct: int, candidates: List[int]) -> Tuple[Dict[str, int], str]:
    """
    For small-integer questions (symmetry) pick 5 options from candidates including correct.
    """
    cand_set = set(candidates)
    cand_set.add(correct)
    opts = set([correct])
    while len(opts) < 5:
        opts.add(random.choice(list(cand_set)))
    opts_list = list(opts)
    random.shuffle(opts_list)
    labels = ["A", "B", "C", "D", "E"]
    correct_letter = labels[opts_list.index(correct)]
    options_dict = {labels[i]: int(opts_list[i]) for i in range(5)}
    return options_dict, correct_letter


# ---------------- Shape question generators ----------------
# Each returns: (question_text, correct_value_or_int, options_dict, correct_letter)
# For symmetry questions, correct_value is small int.

def gen_square(ax):
    s = random.randint(4, 18)
    draw_rect(ax, 0, 0, s, s)
    draw_dimension(ax, 0, s, s, s, s)   # top width
    draw_dimension(ax, 0, 0, 0, s, s)   # left height
    set_tidy_limits(ax, 0, 0, s, s)

    qtype = random.choice(["AREA", "PERIM", "SYMM", "MISSING"])
    if qtype == "AREA":
        correct = s * s
        qtext = "Find the area (cm²) of the square."
        options, letter = generate_mcq_int(correct)
    elif qtype == "PERIM":
        correct = 4 * s
        qtext = "Find the perimeter (cm) of the square."
        options, letter = generate_mcq_int(correct)
    elif qtype == "MISSING":
        # hide one side and give area
        area = s * s
        draw_dimension(ax, 0, s, s, s, "?",)  # top shown as '?'
        qtext = f"The area is {area} cm². Find the side length (cm)."
        correct = s
        options, letter = generate_mcq_int(correct)
    else:
        correct = 4
        qtext = "How many lines of symmetry does the square have?"
        candidates = [0, 1, 2, 3, 4, 6]
        options, letter = generate_mcq_small_candidates(correct, candidates)
    return qtext, options, letter


def gen_rectangle(ax):
    w = random.randint(5, 20)
    h = random.randint(4, 18)
    # ensure not square
    if w == h:
        w += 1
    draw_rect(ax, 0, 0, w, h)
    draw_dimension(ax, 0, h, w, h, w)
    draw_dimension(ax, 0, 0, 0, h, h)
    set_tidy_limits(ax, 0, 0, w, h)

    qtype = random.choice(["AREA", "PERIM", "SYMM", "MISSING"])
    if qtype == "AREA":
        correct = w * h
        qtext = "Find the area (cm²) of the rectangle."
        options, letter = generate_mcq_int(correct)
    elif qtype == "PERIM":
        correct = 2 * (w + h)
        qtext = "Find the perimeter (cm) of the rectangle."
        options, letter = generate_mcq_int(correct)
    elif qtype == "MISSING":
        # hide width, give area
        area = w * h
        draw_dimension(ax, 0, h, w, h, "?")
        qtext = f"The area is {area} cm². Find the width (cm)."
        correct = w
        options, letter = generate_mcq_int(correct)
    else:
        correct = 2
        qtext = "How many lines of symmetry does the rectangle have?"
        candidates = [0, 1, 2, 3, 4]
        options, letter = generate_mcq_small_candidates(correct, candidates)
    return qtext, options, letter


def gen_right_triangle(ax):
    b = random.randint(5, 18)
    h = random.randint(4, 18)
    pts = [(0, 0), (b, 0), (0, h)]
    draw_poly(ax, pts)
    draw_dimension(ax, 0, -0.5, b, -0.5, b)
    draw_dimension(ax, -0.5, 0, -0.5, h, h)
    set_tidy_limits(ax, 0, 0, b, h)

    qtype = random.choice(["AREA", "PERIM", "MISSING"])
    if qtype == "AREA":
        correct = 0.5 * b * h
        qtext = "Find the area (cm²) of the right triangle."
        options, letter = generate_mcq_int(correct)
    elif qtype == "PERIM":
        hyp = math.hypot(b, h)
        correct = int(round(b + h + hyp))
        qtext = "Find the perimeter (cm) of the right triangle (nearest whole number)."
        options, letter = generate_mcq_int(correct)
    else:
        area = int(round(0.5 * b * h))
        # hide base
        draw_dimension(ax, 0, -0.5, b, -0.5, "?")
        qtext = f"The area is {area} cm². Find the base (cm)."
        correct = b
        options, letter = generate_mcq_int(correct)
    return qtext, options, letter


def gen_circle(ax):
    r = random.randint(3, 12)
    circ = Circle((0, 0), r, fill=False, edgecolor="black", linewidth=LINE_W)
    ax.add_patch(circ)
    # draw diameter line for dimension
    draw_line(ax, -r, 0, r, 0)
    draw_dimension(ax, -r, -0.3, r, -0.3, 2 * r)
    set_tidy_limits(ax, -r - 1, -r - 1, r + 1, r + 1)

    qtype = random.choice(["AREA", "PERIM", "MISSING"])
    if qtype == "AREA":
        # instruct to use 3.14; but answers are integers
        correct = int(round(math.pi * r * r))
        qtext = "Find the area (cm²) of the circle (use π ≈ 3.14)."
        options, letter = generate_mcq_int(correct)
    elif qtype == "PERIM":
        correct = int(round(2 * math.pi * r))
        qtext = "Find the circumference (cm) of the circle (use π ≈ 3.14)."
        options, letter = generate_mcq_int(correct)
    else:
        C = int(round(2 * math.pi * r))
        draw_dimension(ax, -r, -0.3, r, -0.3, "?")
        qtext = f"The circumference is {C} cm. Find the radius (cm)."
        correct = r
        options, letter = generate_mcq_int(correct)
    return qtext, options, letter


def gen_parallelogram(ax):
    b = random.randint(6, 18)
    h = random.randint(4, 12)
    slant = random.randint(1, min(6, b - 2))
    pts = [(0, 0), (b, 0), (b + slant, h), (slant, h)]
    draw_poly(ax, pts)
    draw_dimension(ax, 0, -0.4, b, -0.4, b)
    draw_dimension(ax, -0.4 + slant, 0, -0.4 + slant, h, h)
    set_tidy_limits(ax, 0, 0, b + slant, h)

    qtype = random.choice(["AREA", "PERIM", "MISSING"])
    if qtype == "AREA":
        correct = b * h
        qtext = "Find the area (cm²) of the parallelogram."
        options, letter = generate_mcq_int(correct)
    elif qtype == "PERIM":
        side = math.hypot(slant, h)
        correct = int(round(2 * (b + side)))
        qtext = "Find the perimeter (cm) of the parallelogram (nearest whole number)."
        options, letter = generate_mcq_int(correct)
    else:
        area = b * h
        draw_dimension(ax, 0, -0.4, b, -0.4, "?")
        qtext = f"The area is {area} cm². Find the base (cm)."
        correct = b
        options, letter = generate_mcq_int(correct)
    return qtext, options, letter


def gen_trapezium(ax):
    top = random.randint(4, 14)
    bottom = random.randint(top + 2, top + 10)
    h = random.randint(4, 10)
    dx = (bottom - top) / 2.0
    pts = [(0, 0), (bottom, 0), (bottom - dx, h), (dx, h)]
    draw_poly(ax, pts)
    draw_dimension(ax, 0, -0.4, bottom, -0.4, bottom)
    draw_dimension(ax, dx, h + 0.2, bottom - dx, h + 0.2, top)
    draw_dimension(ax, -0.4, 0, -0.4, h, h)
    set_tidy_limits(ax, 0, 0, bottom, h)

    qtype = random.choice(["AREA", "PERIM", "MISSING"])
    if qtype == "AREA":
        correct = int(round((top + bottom) * h / 2.0))
        qtext = "Find the area (cm²) of the isosceles trapezium."
        options, letter = generate_mcq_int(correct)
    elif qtype == "PERIM":
        leg = math.hypot(dx, h)
        correct = int(round(top + bottom + 2 * leg))
        qtext = "Find the perimeter (cm) of the trapezium (nearest whole number)."
        options, letter = generate_mcq_int(correct)
    else:
        area = int(round((top + bottom) * h / 2.0))
        draw_dimension(ax, -0.4, 0, -0.4, h, "?")
        qtext = f"The area is {area} cm². Find the height (cm)."
        correct = h
        options, letter = generate_mcq_int(correct)
    return qtext, options, letter


def gen_L_shape(ax):
    W = random.randint(10, 18)
    H = random.randint(10, 18)
    cut_w = random.randint(3, min(8, W - 4))
    cut_h = random.randint(3, min(8, H - 4))
    # outer rect
    draw_rect(ax, 0, 0, W, H)
    # notch lines (no fill)
    draw_line(ax, W - cut_w, 0, W - cut_w, cut_h)
    draw_line(ax, W - cut_w, cut_h, W, cut_h)
    draw_dimension(ax, 0, H + 0.0, W, H + 0.0, W)
    draw_dimension(ax, -0.4, 0, -0.4, H, H)
    draw_dimension(ax, W - cut_w, cut_h + 0.1, W, cut_h + 0.1, cut_w)
    draw_dimension(ax, W + 0.1, 0, W + 0.1, cut_h, cut_h)
    set_tidy_limits(ax, 0, 0, W, H)

    qtype = random.choice(["AREA", "PERIM", "MISSING"])
    area = W * H - cut_w * cut_h
    if qtype == "AREA":
        correct = area
        qtext = "Find the area (cm²) of the L-shaped figure."
        options, letter = generate_mcq_int(correct)
    elif qtype == "PERIM":
        # compute explicit polygon perimeter by following outer path
        pts = [(0,0),(W,0),(W,cut_h),(W-cut_w,cut_h),(W-cut_w,H),(0,H),(0,0)]
        per = 0.0
        for i in range(len(pts)-1):
            per += math.hypot(pts[i+1][0]-pts[i][0], pts[i+1][1]-pts[i][1])
        correct = int(round(per))
        qtext = "Find the perimeter (cm) of the L-shaped figure (nearest whole number)."
        options, letter = generate_mcq_int(correct)
    else:
        draw_dimension(ax, W - cut_w, cut_h + 0.1, W, cut_h + 0.1, "?")
        qtext = f"The area is {area} cm². Find the notch width (cm)."
        correct = cut_w
        options, letter = generate_mcq_int(correct)
    return qtext, options, letter


def gen_T_shape(ax):
    base_w = random.randint(8, 16)
    base_h = random.randint(3, 6)
    top_w = random.randint(base_w + 2, base_w + 8)
    top_h = random.randint(3, 6)
    left = -(top_w - base_w) / 2.0
    # base
    draw_rect(ax, 0, 0, base_w, base_h)
    # top
    draw_rect(ax, left, base_h, top_w, top_h)
    draw_dimension(ax, 0, base_h, base_w, base_h, base_w)
    draw_dimension(ax, left, base_h + top_h, left + top_w, base_h + top_h, top_w)
    draw_dimension(ax, -0.4, 0, -0.4, base_h, base_h)
    set_tidy_limits(ax, min(0, left), 0, max(base_w, left + top_w), base_h + top_h)

    qtype = random.choice(["AREA", "PERIM", "MISSING"])
    area = base_w * base_h + top_w * top_h
    if qtype == "AREA":
        correct = area
        qtext = "Find the area (cm²) of the T-shaped figure."
        options, letter = generate_mcq_int(correct)
    elif qtype == "PERIM":
        # poly perimeter
        pts = [(left, base_h + top_h),(left+top_w, base_h + top_h),(left+top_w, base_h),
               (base_w, base_h),(base_w,0),(0,0),(0,base_h),(left,base_h),(left, base_h+top_h)]
        per = 0.0
        for i in range(len(pts)-1):
            per += math.hypot(pts[i+1][0]-pts[i][0], pts[i+1][1]-pts[i][1])
        correct = int(round(per))
        qtext = "Find the perimeter (cm) of the T-shaped figure (nearest whole number)."
        options, letter = generate_mcq_int(correct)
    else:
        draw_dimension(ax, left, base_h + top_h, left + top_w, base_h + top_h, "?")
        qtext = f"The area is {area} cm². Find the top width (cm)."
        correct = top_w
        options, letter = generate_mcq_int(correct)
    return qtext, options, letter


def gen_cross(ax):
    arm_w = random.randint(3, 6)
    arm_l = random.randint(7, 12)
    total = 2 * arm_l - arm_w
    cx = cy = arm_l
    # vertical rectangle
    draw_rect(ax, cx - arm_w / 2.0, cy - total / 2.0, arm_w, total)
    # horizontal rectangle
    draw_rect(ax, cx - total / 2.0, cy - arm_w / 2.0, total, arm_w)
    draw_dimension(ax, cx - total / 2.0, cy + arm_w / 2.0 + 0.1, cx + total / 2.0, cy + arm_w / 2.0 + 0.1, total)
    draw_dimension(ax, cx + arm_w / 2.0 + 0.1, cy - total / 2.0, cx + arm_w / 2.0 + 0.1, cy + total / 2.0, total)
    set_tidy_limits(ax, cx - total / 2.0, cy - total / 2.0, cx + total / 2.0, cy + total / 2.0)

    qtype = random.choice(["AREA", "PERIM", "MISSING"])
    # compute area: union of two rectangles minus overlapping square
    area = (total * arm_w) + (total * arm_w) - (arm_w * arm_w)
    if qtype == "AREA":
        correct = area
        qtext = "Find the area (cm²) of the cross-shaped figure."
        options, letter = generate_mcq_int(correct)
    elif qtype == "PERIM":
        # compute outer polygon perimeter (approx by building polygon)
        t = total
        w = arm_w
        pts = [
            (cx - t/2, cy - w/2),
            (cx - w/2, cy - w/2),
            (cx - w/2, cy - t/2),
            (cx + w/2, cy - t/2),
            (cx + w/2, cy - w/2),
            (cx + t/2, cy - w/2),
            (cx + t/2, cy + w/2),
            (cx + w/2, cy + w/2),
            (cx + w/2, cy + t/2),
            (cx - w/2, cy + t/2),
            (cx - w/2, cy + w/2),
            (cx - t/2, cy + w/2),
            (cx - t/2, cy - w/2)
        ]
        per = 0.0
        for i in range(len(pts)-1):
            per += math.hypot(pts[i+1][0]-pts[i][0], pts[i+1][1]-pts[i][1])
        correct = int(round(per))
        qtext = "Find the perimeter (cm) of the cross-shaped figure (nearest whole number)."
        options, letter = generate_mcq_int(correct)
    else:
        draw_dimension(ax, cx - total / 2.0, cy + arm_w / 2.0 + 0.1, cx + total / 2.0, cy + arm_w / 2.0 + 0.1, "?")
        qtext = f"The area is {area} cm². Find the arm thickness (cm)."
        correct = arm_w
        options, letter = generate_mcq_int(correct)
    return qtext, options, letter


# Pool of generator functions
GEN_FUNCS = [
    gen_square,
    gen_rectangle,
    gen_right_triangle,
    gen_circle,
    gen_parallelogram,
    gen_trapezium,
    gen_L_shape,
    gen_T_shape,
    gen_cross
]


# ---------------- Main generation loop ----------------
def main():
    ensure_dirs()
    out_data: List[Dict[str, Any]] = []

    for i in range(1, NUM_QUESTIONS + 1):
        fig, ax = plt.subplots(figsize=FIGSIZE)
        ax.set_aspect("equal")
        ax.axis("off")

        gen = random.choice(GEN_FUNCS)
        qtext, options, correct_letter = gen(ax)

        # Save image (no question/options text in image)
        img_name = f"Q{i}.png"
        img_path = os.path.join(IMG_DIR, img_name)
        plt.savefig(img_path, dpi=DPI, bbox_inches="tight", pad_inches=0.2)
        plt.close(fig)

        # Build object
        obj = {
            "id": f"Q{i}",
            "question": qtext,
            "options": options,    # dict {"A": int, ...}
            "answer": correct_letter,
            "image": img_path
        }
        out_data.append(obj)

        # Progress printing occasionally
        if i % 100 == 0:
            print(f"Generated {i} / {NUM_QUESTIONS}")

    # Write JSON array
    with open(JSON_PATH, "w") as f:
        json.dump(out_data, f, indent=2)

    print("✅ Done.")
    print(f"Images saved to ./{IMG_DIR}/")
    print(f"Questions JSON saved to ./{JSON_PATH}")


if __name__ == "__main__":
    main()
