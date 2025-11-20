import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import random

# Directions and their vector representation
DIRECTIONS = {
    "north": (-1, 0),
    "south": (1, 0),
    "east": (0, 1),
    "west": (0, -1),
    "north-east": (-1, 1),
    "north-west": (-1, -1),
    "south-east": (1, 1),
    "south-west": (1, -1)
}

UK_NAMES = ["Olivia", "George", "Harry", "Amelia", "Jack", "Emily", "Tom", "Isla", "James", "Freya"]
LABELS = ["A", "B", "C", "D", "E"]

def generate_question_and_plot(q_num, pdf):
    grid_size = 5
    start = (2, 2)  # Always the center
    name = random.choice(UK_NAMES)

    # Random directions and steps
    dir1 = random.choice(list(DIRECTIONS.keys()))
    dir2 = random.choice(list(DIRECTIONS.keys()))
    steps1 = random.randint(1, 2)
    steps2 = random.randint(1, 2)

    # First movement
    r1 = start[0] + DIRECTIONS[dir1][0] * steps1
    c1 = start[1] + DIRECTIONS[dir1][1] * steps1

    # Second movement
    final = (
        r1 + DIRECTIONS[dir2][0] * steps2,
        c1 + DIRECTIONS[dir2][1] * steps2
    )

    # Validate final position within grid
    if not (0 <= final[0] < grid_size and 0 <= final[1] < grid_size):
        return generate_question_and_plot(q_num)

    # Place labels randomly
    label_positions = random.sample([(r, c) for r in range(grid_size) for c in range(grid_size) if (r, c) != start], 5)
    label_map = {pos: label for pos, label in zip(label_positions, LABELS)}

    # Plotting
    fig, ax = plt.subplots()
    for x in range(grid_size + 1):
        ax.plot([0, grid_size], [x, x], color='black')
        ax.plot([x, x], [0, grid_size], color='black')

    for pos, label in label_map.items():
        ax.text(pos[1] + 0.5, grid_size - pos[0] - 0.5, label, ha='center', va='center', fontsize=14)

    # Plot start position
    ax.text(start[1] + 0.5, grid_size - start[0] - 0.5, 'X', ha='center', va='center', fontsize=14, color='red')

    ax.set_xlim(0, grid_size)
    ax.set_ylim(0, grid_size)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect('equal')

    question_text = f"{name} starts on the cross and moves {steps1} square{'s' if steps1 > 1 else ''} to the {dir1}.\n" \
                    f"They then move {steps2} square{'s' if steps2 > 1 else ''} in the direction of {dir2}.\n" \
                    f"On what square do they end up? A, B, C, D or E?"

    plt.title(f"Q{q_num}: {question_text}", fontsize=10)
    plt.tight_layout()

    # Save the figure to the PDF
    pdf.savefig(fig)
    plt.close(fig)
    
    #plt.show()

    # Get correct answer
    answer = label_map.get(final, "None")
    print(f"Q{q_num} Answer: {answer}\n")

#def generate_multiple_questions(n=5):
#    for i in range(1, n + 1):
#        generate_question_and_plot(i)

# Generate 5 random questions
generate_multiple_questions(5)
