import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Polygon, Arc, Circle, Wedge, Rectangle
import numpy as np
import os
from datetime import datetime

# Create images directory
os.makedirs('images', exist_ok=True)

def save_geometry_figure(fig, question_id):
    """Save figure to images folder with consistent naming"""
    filepath = f'images/geometry_q{question_id}.png'
    fig.patch.set_facecolor('white')
    fig.savefig(filepath, dpi=150, bbox_inches='tight', 
                facecolor='white', pad_inches=0.1)
    plt.close(fig)
    return filepath

def create_triangle_classification_question(q_id):
    fig, ax = plt.subplots(figsize=(12, 9))
    
    # Create isosceles triangle with shading
    triangle = np.array([[2, 2], [8, 2], [5, 7], [2, 2]])
    ax.fill(triangle[:, 0], triangle[:, 1], 
            color='lightblue', alpha=0.7, edgecolor='navy', linewidth=3)
    
    # Add labels
    ax.text(5, 1.5, '8 cm', fontsize=16, ha='center',
            bbox=dict(boxstyle='round', fc='yellow', alpha=0.8))
    ax.text(2.8, 4.5, '6 cm', fontsize=16, rotation=60,
            bbox=dict(boxstyle='round', fc='yellow', alpha=0.8))
    ax.text(7.2, 4.5, '6 cm', fontsize=16, rotation=-60,
            bbox=dict(boxstyle='round', fc='yellow', alpha=0.8))
    
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 9)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Shaded Triangle', fontsize=20, fontweight='bold', pad=20)
    
    filepath = save_geometry_figure(fig, q_id)
    
    question = {
        "question": "The blue shaded triangle has two sides of equal length (6 cm each). What type of triangle is this?",
        "options": {
            "A": "Equilateral triangle",
            "B": "Isosceles triangle",
            "C": "Scalene triangle",
            "D": "Right-angled triangle"
        },
        "answer": "B",
        "imageFilePath": filepath,
        "difficulty": "easy",
        "used": 0
    }
    
    return question

def create_shaded_region_question(q_id):
    fig, ax = plt.subplots(figsize=(12, 9))
    
    # Rectangle (unshaded)
    rect = Rectangle((1.5, 2), 7, 5, 
                     fill=True, facecolor='white', 
                     edgecolor='black', linewidth=3)
    ax.add_patch(rect)
    
    # Shaded triangle inside
    triangle = np.array([[1.5, 2], [8.5, 2], [8.5, 7], [1.5, 2]])
    ax.fill(triangle[:, 0], triangle[:, 1], 
            color='lightgreen', alpha=0.7, edgecolor='darkgreen', linewidth=3)
    
    # Right angle marker
    ax.plot([8.2, 8.2, 8.5], [2, 2.3, 2.3], 'k-', linewidth=2)
    ax.plot([8.2, 8.5], [2, 2], 'k-', linewidth=2)
    
    # Label
    ax.text(6, 4, 'Shaded\nRegion', fontsize=18, ha='center',
            fontweight='bold', color='darkgreen')
    
    ax.set_xlim(0.5, 9.5)
    ax.set_ylim(1, 8)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Rectangle with Shaded Triangle', fontsize=20, 
                 fontweight='bold', pad=20)
    
    filepath = save_geometry_figure(fig, q_id)
    
    question = {
        "question": "What type of triangle is the green shaded region?",
        "options": {
            "A": "Right-angled triangle",
            "B": "Equilateral triangle",
            "C": "Obtuse triangle",
            "D": "Acute triangle"
        },
        "answer": "A",
        "imageFilePath": filepath,
        "difficulty": "easy",
        "used": 0
    }
    
    return question

def create_angle_question(q_id):
    fig, ax = plt.subplots(figsize=(12, 9))
    
    # Draw angle lines
    ax.plot([1, 7], [3, 3], 'b-', linewidth=4)
    ax.plot([7, 9], [3, 5.5], 'b-', linewidth=4)
    
    # Draw arc showing angle
    arc = Arc((7, 3), 1.5, 1.5, angle=0, theta1=0, theta2=45, 
              color='red', linewidth=3)
    ax.add_patch(arc)
    
    # Angle measurement
    ax.text(7.8, 3.6, '55°', fontsize=22, color='red', fontweight='bold',
            bbox=dict(boxstyle='round', fc='white', alpha=0.9))
    
    # Vertex labels
    ax.text(7, 2.4, 'B', fontsize=18, ha='center', fontweight='bold')
    ax.text(0.5, 3, 'A', fontsize=18, ha='center', fontweight='bold')
    ax.text(9.5, 5.5, 'C', fontsize=18, ha='center', fontweight='bold')
    
    ax.set_xlim(0, 10.5)
    ax.set_ylim(1.5, 6.5)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('∠ABC = 55°', fontsize=22, fontweight='bold', pad=20)
    
    filepath = save_geometry_figure(fig, q_id)
    
    question = {
        "question": "Angle ABC measures 55°. What type of angle is this?",
        "options": {
            "A": "Acute angle",
            "B": "Right angle",
            "C": "Obtuse angle",
            "D": "Straight angle"
        },
        "answer": "A",
        "imageFilePath": filepath,
        "difficulty": "easy",
        "used": 0
    }
    
    return question

def create_sector_question(q_id):
    fig, ax = plt.subplots(figsize=(12, 9))
    
    # Full circle (unshaded)
    circle = Circle((5, 5), 3, fill=False, edgecolor='black', linewidth=3)
    ax.add_patch(circle)
    
    # Shaded sector (90 degrees)
    theta = np.linspace(0, np.pi/2, 100)
    x = 5 + 3 * np.cos(theta)
    y = 5 + 3 * np.sin(theta)
    vertices = np.column_stack([np.concatenate([[5], x, [5]]), 
                                np.concatenate([[5], y, [5]])])
    sector = Polygon(vertices, facecolor='orange', 
                    alpha=0.7, edgecolor='darkorange', linewidth=3)
    ax.add_patch(sector)
    
    # Center point
    ax.plot(5, 5, 'ko', markersize=8)
    
    # Radius lines
    ax.plot([5, 8], [5, 5], 'k-', linewidth=2)
    ax.plot([5, 5], [5, 8], 'k-', linewidth=2)
    
    # Label
    ax.text(6.5, 6.5, 'Shaded\nSector', fontsize=16, 
            ha='center', fontweight='bold')
    
    # Angle arc
    arc = Arc((5, 5), 1, 1, angle=0, theta1=0, theta2=90, 
              color='red', linewidth=3)
    ax.add_patch(arc)
    ax.text(5.6, 5.3, '90°', fontsize=14, color='red', fontweight='bold')
    
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Circle with Shaded Sector', fontsize=20, 
                 fontweight='bold', pad=20)
    
    filepath = save_geometry_figure(fig, q_id)
    
    question = {
        "question": "What angle does the orange shaded sector make at the center?",
        "options": {
            "A": "90°",
            "B": "45°",
            "C": "180°",
            "D": "60°"
        },
        "answer": "A",
        "imageFilePath": filepath,
        "difficulty": "easy",
        "used": 0
    }
    
    return question

def create_concentric_circles_question(q_id):
    fig, ax = plt.subplots(figsize=(12, 9))
    
    # Outer circle
    outer_circle = Circle((5, 5), 3.5, fill=False, 
                          edgecolor='black', linewidth=3)
    ax.add_patch(outer_circle)
    
    # Shaded ring (between outer and inner)
    theta = np.linspace(0, 2*np.pi, 100)
    # Outer edge
    x_outer = 5 + 3.5 * np.cos(theta)
    y_outer = 5 + 3.5 * np.sin(theta)
    # Inner edge
    x_inner = 5 + 2 * np.cos(theta)
    y_inner = 5 + 2 * np.sin(theta)
    
    ax.fill(x_outer, y_outer, color='lightblue', alpha=0.7)
    ax.fill(x_inner, y_inner, color='white', alpha=1)
    
    # Inner circle border
    inner_circle = Circle((5, 5), 2, fill=False, 
                          edgecolor='black', linewidth=3)
    ax.add_patch(inner_circle)
    
    # Labels
    ax.text(5, 5, 'White\nCenter', fontsize=14, ha='center', 
            fontweight='bold')
    ax.text(5, 7.2, 'Blue Ring\n(Shaded)', fontsize=14, ha='center',
            fontweight='bold', color='darkblue')
    
    # Radii
    ax.plot([5, 5], [5, 8.5], 'k--', linewidth=2)
    ax.text(5.3, 6.7, '3.5 cm', fontsize=12, rotation=90)
    ax.plot([5, 5], [5, 7], 'k-', linewidth=2)
    ax.text(4.5, 6, '2 cm', fontsize=12, rotation=90)
    
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Concentric Circles', fontsize=20, 
                 fontweight='bold', pad=20)
    
    filepath = save_geometry_figure(fig, q_id)
    
    question = {
        "question": "What is the shaded region between the two circles called?",
        "options": {
            "A": "Ring or annulus",
            "B": "Sector",
            "C": "Segment",
            "D": "Diameter"
        },
        "answer": "A",
        "imageFilePath": filepath,
        "difficulty": "easy",
        "used": 0
    }
    
    return question

def create_symmetry_question(q_id):
    fig, ax = plt.subplots(figsize=(12, 9))
    
    # Symmetrical shape (heart)
    t = np.linspace(0, 2*np.pi, 1000)
    x = 16 * np.sin(t)**3
    y = 13 * np.cos(t) - 5 * np.cos(2*t) - 2 * np.cos(3*t) - np.cos(4*t)
    x = x / 4 + 5
    y = y / 4 + 5
    
    ax.fill(x, y, color='pink', alpha=0.7, edgecolor='red', linewidth=3)
    
    # Line of symmetry
    ax.plot([5, 5], [0.5, 8.5], 'b--', linewidth=3, 
            label='Line of Symmetry')
    
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 9)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Heart Shape with Line of Symmetry', 
                 fontsize=20, fontweight='bold', pad=20)
    ax.legend(fontsize=14, loc='upper right')
    
    filepath = save_geometry_figure(fig, q_id)
    
    question = {
        "question": "How many lines of symmetry does this heart shape have?",
        "options": {
            "A": "1",
            "B": "2",
            "C": "4",
            "D": "0"
        },
        "answer": "A",
        "imageFilePath": filepath,
        "difficulty": "easy",
        "used": 0
    }
    
    return question

def create_intersection_question(q_id):
    fig, ax = plt.subplots(figsize=(12, 9))
    
    # Circle 1 (left) - semi-transparent
    circle1 = Circle((4, 5), 2.5, fill=True, facecolor='red', 
                     alpha=0.4, edgecolor='darkred', linewidth=3)
    ax.add_patch(circle1)
    
    # Circle 2 (right) - semi-transparent
    circle2 = Circle((6, 5), 2.5, fill=True, facecolor='blue', 
                     alpha=0.4, edgecolor='darkblue', linewidth=3)
    ax.add_patch(circle2)
    
    # Labels
    ax.text(3, 5, 'Red\nCircle', fontsize=14, ha='center', 
            fontweight='bold', color='darkred')
    ax.text(7, 5, 'Blue\nCircle', fontsize=14, ha='center',
            fontweight='bold', color='darkblue')
    ax.text(5, 5, 'Purple\nOverlap', fontsize=12, ha='center',
            fontweight='bold', color='purple')
    
    ax.set_xlim(0, 10)
    ax.set_ylim(1, 9)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Two Overlapping Circles', fontsize=20,
                 fontweight='bold', pad=20)
    
    filepath = save_geometry_figure(fig, q_id)
    
    question = {
        "question": "When the red and blue circles overlap, what color is the intersection region?",
        "options": {
            "A": "Purple",
            "B": "Green",
            "C": "Orange",
            "D": "Yellow"
        },
        "answer": "A",
        "imageFilePath": filepath,
        "difficulty": "easy",
        "used": 0
    }
    
    return question

def generate_all_geometry_questions():
    """Generate all geometry questions and save to JSON"""
    
    questions = []
    
    # Generate different types of questions
    questions.append(create_triangle_classification_question(1))
    questions.append(create_shaded_region_question(2))
    questions.append(create_angle_question(3))
    questions.append(create_sector_question(4))
    questions.append(create_concentric_circles_question(5))
    questions.append(create_symmetry_question(6))
    questions.append(create_intersection_question(7))
    
    # Add more question types...
    # You can create variations by calling functions with different parameters
    
    # Save to JSON
    output = {
        "metadata": {
            "title": "Year 6 Geometry - Properties of Shapes",
            "total_questions": len(questions),
            "difficulty": "easy",
            "curriculum": "UK National Curriculum",
            "generated_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "questions": questions
    }
    
    with open('geometry_questions.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✓ Generated {len(questions)} questions")
    print(f"✓ Images saved to 'images/' folder")
    print(f"✓ JSON saved to 'geometry_questions.json'")
    
    return output

# Run the generation
if __name__ == "__main__":
    result = generate_all_geometry_questions()
