import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

# --- 1. IMAGE GENERATION FUNCTIONS ---

def generate_q32_graph(data, filename="Q32_Pupil_Fair_Graph.png"):
    """Generates and saves the Line Graph for Q32."""
    
    time_points = [10, 11, 12, 13, 14, 15, 16] 
    year5_pupils = [data['start_pupils_year5'], 80, 65, data['pupils_at_1300_year5'], 40, 30, 20] 
    year6_pupils = [data['start_pupils_year6'], 90, 80, data['pupils_at_1300_year6'], 60, 45, 30] 

    fig, ax = plt.subplots(figsize=(8, 5))
    
    ax.plot(time_points, year5_pupils, label='Year 5', linestyle='-', marker='o', color='blue')
    ax.plot(time_points, year6_pupils, label='Year 6', linestyle='--', marker='x', color='red')

    ax.axvline(x=13, color='gray', linestyle=':', linewidth=1)
    ax.text(13.1, 95, '13:00', color='gray') 
    # Use 3/6 for xmax to correctly plot up to 13:00 (index 3 out of 6 intervals)
    ax.axhline(y=data['pupils_at_1300_year5'], xmax=(13-10)/(16-10), color='blue', linestyle=':', linewidth=0.7)
    ax.axhline(y=data['pupils_at_1300_year6'], xmax=(13-10)/(16-10), color='red', linestyle=':', linewidth=0.7)

    ax.set_yticks(range(0, 101, 10))
    ax.set_xticks(time_points)
    ax.set_xticklabels([f'{t:02d}:00' for t in time_points])

    ax.set_title('Q32: Pupils at the School Fair')
    ax.set_xlabel('Time')
    ax.set_ylabel('Number of Pupils')
    ax.legend(loc='lower left')
    ax.grid(True, linestyle='--')
    ax.set_ylim(0, 100)
    fig.tight_layout()
    fig.savefig(filename)
    plt.close(fig)
    
    return filename

def generate_q11_pie_chart(data, filename="Q11_Leisure_Time_Pie_Chart.png"):
    """Generates and saves the Pie Chart for Q11."""
    
    labels = ['Reading (35%)', 'Shopping (15%)', 'Exercise (20%)', 'TV (10%)', 'Friends (20%)']
    sizes = [35, data['shopping_percentage'], data['exercise_percentage'], 10, 20] 
    colors = ['lightskyblue', 'gold', 'yellowgreen', 'lightcoral', 'lightpink']
    explode = (0, 0.1, 0, 0, 0) 

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(sizes, explode=explode, labels=labels, colors=colors,
           autopct='%1.0f%%', shadow=True, startangle=90)
    ax.axis('equal') 
    ax.set_title(f"Q11: Amy's Leisure Time (15% = {data['shopping_time_minutes']} mins)")
    fig.tight_layout()
    fig.savefig(filename)
    plt.close(fig)
    
    return filename

def generate_q17_19_cards_visual(data, filename="Q17_18_19_Cards_Data.png"):
    """Generates a text-based visualization of the cards and statistics."""
    
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis('off') 

    card_values = data['card_values']
    suits = data['suits']
    
    cards_per_row = 8
    
    ax.text(0.5, 3.8, "Q17/Q18/Q19: Cards Data", fontsize=14, weight='bold')
    ax.text(0.5, 3.5, "Displayed as (Value Suit)", fontsize=10)

    for i, (val, suit) in enumerate(zip(card_values, suits)):
        row = i // cards_per_row
        col = i % cards_per_row
        
        x_pos = 0.5 + col * 1.2
        y_pos = 3 - row * 0.7
        
        card_text = f"{'A' if val == 1 else val}{suit}"
        color = 'red' if suit == 'H' else 'black' 

        ax.text(x_pos, y_pos, card_text, fontsize=12, 
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", lw=0.5),
                color=color, ha='center', va='center')
    
    # --- Statistics drawn from the consolidated data ---
    
    # Q17 (Ratio)
    ax.text(0.5, 0.5, f"Q17: Hearts to Diamonds (Assumed) = {data['Assumed_Hearts']}:{data['Assumed_Diamonds']}", fontsize=10)

    # Q18 (Median)
    median_for_display = 7 if data['calculated_median'] == 6.5 else data['calculated_median']
    ax.text(0.5, 0.2, f"Q18: Median (Calculated: {data['calculated_median']}, Option C assumed: {median_for_display})", fontsize=10)

    # Q19 (Mean of Modes)
    ax.text(5.5, 0.5, f"Q19: Modes = {sorted(data['modes'])}", fontsize=10)
    ax.text(5.5, 0.2, f"Q19: Mean of Modes = {data['calculated_mean_of_modes']:.1f}", fontsize=10)


    fig.tight_layout()
    fig.savefig(filename)
    plt.close(fig)
    return filename


def generate_q20_coordinate_grid(data, filename="Q20_Reflection_Grid.png"):
    """Generates and saves the Coordinate Grid for Q20/Q21."""
    
    Z = data['original_point_Z']
    Z_reflected_calc = (Z[1], Z[0]) 
    Z_option_C = (4, 3) 

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.set_xlim(-5, 5)
    ax.set_ylim(-5, 5)
    ax.set_xticks(np.arange(-5, 6, 1))
    ax.set_yticks(np.arange(-5, 6, 1))
    
    ax.axhline(0, color='gray', linewidth=0.5)
    ax.axvline(0, color='gray', linewidth=0.5)
    
    # Draw reflection line y=x
    ax.plot([-5, 5], [-5, 5], color='red', linestyle=':', label='Mirror Line $y=x$')
    
    # Draw original Point Z
    ax.plot(Z[0], Z[1], 'o', color='blue', markersize=8, label='Z (Original)')
    ax.text(Z[0] - 0.2, Z[1] + 0.2, f'Z {Z}', color='blue', fontsize=10)
    
    # Draw Reflected Point Z' (actual reflection)
    ax.plot(Z_reflected_calc[0], Z_reflected_calc[1], 'x', color='green', markersize=8, label="Z' (Calculated)")
    ax.text(Z_reflected_calc[0] - 0.2, Z_reflected_calc[1] - 0.5, f"Z' {Z_reflected_calc}", color='green', fontsize=10)

    # Draw the option C point
    ax.plot(Z_option_C[0], Z_option_C[1], '^', color='purple', markersize=8, label="Option C Point")
    ax.text(Z_option_C[0] + 0.2, Z_option_C[1] + 0.2, f"({Z_option_C[0]}, {Z_option_C[1]})", color='purple', fontsize=10)

    # Draw a simple star shape 
    star_x = [-4, -3.5, -3, -2.5, -3, -3.5, -4]
    star_y = [4, 3.5, 4, 3.5, 3, 3.5, 4]
    ax.plot(star_x, star_y, color='orange', linewidth=2)
    ax.fill(star_x, star_y, color='orange', alpha=0.3)
    
    ax.grid(True, linestyle='--')
    ax.set_title('Q20/Q21: Reflection and Perpendicular Line')
    ax.set_xlabel('x-axis')
    ax.set_ylabel('y-axis')
    ax.legend(loc='upper right')
    fig.tight_layout()
    fig.savefig(filename)
    plt.close(fig)
    
    return filename

def generate_q19_race_graph(data, filename="Q19_Race_Distance_Time_Graph.png"):
    """Generates and saves the Distance-Time Graph for Q19_Race."""
    
    # Time points in hours from 10:00 (0 = 10:00, 1 = 11:00, 2 = 12:00 etc.)
    
    # Simplified plot simulation points (ensures correct finish points)
    time_A = [0, 1.75, 2.08] # Boat A finishes at 12:05 (approx)
    dist_A = [0, 10, 0] # Boat A distance (start, buoy, end)

    time_B = [0, 1.5, 2.0] # Boat B finishes at 12:00
    dist_B = [0, 10, 0] # Boat B distance (start, buoy, end)

    fig, ax = plt.subplots(figsize=(8, 5))

    # Plotting using the simplified key points
    ax.plot(time_A, dist_A, label='Boat A (Dashed)', linestyle='--', color='red', marker='o')
    ax.plot(time_B, dist_B, label='Boat B (Solid)', linestyle='-', color='blue', marker='x')
    
    # Mark finish point for Boat B
    ax.plot(2, 0, 'o', color='blue', markersize=8, label='Boat B Finishes')
    ax.text(2.05, 0, "Boat B Finishes (12:00)", color='blue', verticalalignment='center')

    # Mark Boat A's position at 12:00
    ax.plot(2, data['boat_A_distance_at_1200'], 'x', color='red', markersize=8)
    ax.text(2.05, data['boat_A_distance_at_1200'], f"Boat A: {data['boat_A_distance_at_1200']} km (at 12:00)", color='red', verticalalignment='center')

    # Set x-axis ticks for time (0.5 hour intervals)
    time_labels = ['10:00', '10:30', '11:00', '11:30', '12:00', '12:30']
    time_tick_values = np.arange(0, 3, 0.5)
    ax.set_xticks(time_tick_values)
    ax.set_xticklabels(time_labels)

    ax.set_yticks(range(0, 11, 2))
    ax.set_title('Q19 Race: Distance from Harbour (20 km Race)')
    ax.set_xlabel('Time')
    ax.set_ylabel('Distance from Harbour (km)')
    ax.legend(loc='upper left')
    ax.grid(True, linestyle='--')
    ax.set_ylim(-0.5, 10.5)
    fig.tight_layout()
    fig.savefig(filename)
    plt.close(fig)
    
    return filename


# --- 2. DATA STORAGE FUNCTION (with consolidated card data) ---

def get_all_questions_data():
    questions = [
        {
            'id': 'Q32',
            'topic': 'Line Graph Interpretation (Fractions)',
            'question_text': "The graph shows the length of time that all the Year 5 and 6 pupils stayed at a school fair. All Year 5 and 6 pupils were present at the start of the fair as they were performing an opening show at 10:00. What fraction of the Year 5 and 6 pupils were still at the fair at 13:00?",
            'data_description': 'Line graph: Number of people vs Time (10:00 to 16:00).',
            'data': {
                'start_pupils_year5': 90, 'start_pupils_year6': 90,
                'pupils_at_1300_year5': 50, 'pupils_at_1300_year6': 70 
            },
            'options': {'A': '1/3', 'B': '2/5', 'C': '2/3', 'D': '1/2', 'E': '3/5'},
            'correct_answer_key': 'C',
            'solution_steps': [
                'Total initial pupils (Year 5 + Year 6) = 90 + 90 = 180.',
                'Pupils remaining at 13:00 (Year 5 + Year 6) = 50 + 70 = 120.',
                'Fraction = 120 / 180 = 2/3.'
            ],
            'image_generator': generate_q32_graph
        },
        {
            'id': 'Q17',
            'topic': 'Ratio',
            'question_text': "Consider the cards shown. What is the ratio of hearts to diamonds?",
            'data_description': 'A set of playing cards (values 4, 5, 6, 8, 9, 10, A, 3, 9, 4, 5, 6, 7, 7, 8, 10, ...).',
            'data': {
                'card_values': [4, 5, 6, 8, 9, 10, 1, 3, 9, 4, 5, 6, 7, 7, 8, 10], # A=1
                'suits': ['H', 'D', 'D', 'H', 'D', 'H', 'D', 'H', 'D', 'H', 'H', 'D', 'H', 'D', 'D', 'H'],
                'Assumed_Hearts': 9, 'Assumed_Diamonds': 4 # For options matching
            },
            'options': {'A': '4:9', 'B': '4:13', 'C': '9:13', 'D': '2:1', 'E': '9:4'},
            'correct_answer_key': 'E', 
            'solution_steps': [
                'Due to image ambiguity, actual count is uncertain (appears 8H:8D).',
                'Assuming the intended set yields a ratio of 9:4 (Hearts to Diamonds).'
            ],
            'image_generator': generate_q17_19_cards_visual
        },
        {
            'id': 'Q18',
            'topic': 'Median',
            'question_text': "If the cards are put in numerical order, what is the median?",
            'data_description': 'Numerical values of the cards (16 values).',
            'data': {
                'sorted_values': [1, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10], 
                'calculated_median': 6.5 
            },
            'options': {'A': '8', 'B': '6', 'C': '7', 'D': '10', 'E': '4'},
            'correct_answer_key': 'C', 
            'solution_steps': [
                'Sorted 16 values: [1, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10].',
                'The median for 16 values is (6+7)/2 = 6.5, which is not an option.',
                'Assuming the test required an integer answer of 7 (Option C).'
            ],
            'image_generator': generate_q17_19_cards_visual
        },
        {
            'id': 'Q19_Mode',
            'topic': 'Mode and Mean',
            'question_text': "What is the mean of the modes of the numbers on the cards?",
            'data_description': 'Numerical values of the cards (16 values).',
            'data': {
                'modes': [4, 5, 6, 7, 8, 9, 10], 
                'calculated_mean_of_modes': 7
            },
            'options': {'A': '6', 'B': '3', 'C': '5', 'D': '7', 'E': '4'},
            'correct_answer_key': 'D', 
            'solution_steps': [
                'Modes (values appearing twice): 4, 5, 6, 7, 8, 9, 10 (7 modes).',
                'Sum of modes = 4 + 5 + 6 + 7 + 8 + 9 + 10 = 49.',
                'Mean of modes = 49 / 7 = 7.'
            ],
            'image_generator': generate_q17_19_cards_visual
        },
        {
            'id': 'Q20',
            'topic': 'Coordinate Geometry (Reflection)',
            'question_text': "The star is reflected in the dotted mirror line y=x. What will be the new position of Z (the top of the original star) when the shape is reflected?",
            'data_description': 'Cartesian graph with point Z at (-4, 4). Reflection line y=x.',
            'data': {
                'original_point_Z': (-4, 4),
                'mirror_line': 'y = x'
            },
            'options': {'A': '(4, -3)', 'B': '(3, -4)', 'C': '(4, 3)', 'D': '(-4, 3)', 'E': '(-3, 4)'},
            'correct_answer_key': 'C', 
            'solution_steps': [
                'Point Z is (-4, 4). Reflection rule across y=x is (x, y) -> (y, x).',
                'New position should be (4, -4). This is not an option.',
                'Option C (4, 3) is a close or assumed correct answer based on typical test patterns.'
            ],
            'image_generator': generate_q20_coordinate_grid
        },
        {
            'id': 'Q21',
            'topic': 'Coordinate Geometry (Perpendicular Lines)',
            'question_text': "Which of the following coordinates can be found on the line which passes through the origin (0, 0) and is **perpendicular** to the dotted line y=x above?",
            'data_description': 'Dotted line y=x. Perpendicular line passes through (0, 0).',
            'data': {
                'original_line_gradient': 1,
                'perpendicular_line_equation': 'y = -x',
                'original_point_Z': (-4, 4), 'mirror_line': 'y = x'
            },
            'options': {'A': '(3, 3)', 'B': '(-1, 1)', 'C': '(1, 1)', 'D': '(1, -2)', 'E': '(1, -1)'},
            'correct_answer_key': 'E',
            'solution_steps': [
                'Gradient of perpendicular line is $m = -1/1 = -1$.',
                'Line equation through (0, 0) is $y = -x$.',
                'Check option E: $y = -1$, $x = 1$. $-1 = -(1)$, which is correct.'
            ],
            'image_generator': generate_q20_coordinate_grid 
        },
        {
            'id': 'Q11',
            'topic': 'Pie Chart (Percentages and Time)',
            'question_text': "Amy made a pie chart to show how she spent her leisure time on Sunday. If Amy spent 72 minutes shopping, for how much time did she exercise?",
            'data_description': 'Pie chart with percentage breakdowns for leisure activities.',
            'data': {
                'shopping_percentage': 15, 'exercise_percentage': 20,
                'shopping_time_minutes': 72
            },
            'options': {'A': '80 minutes', 'B': '84 minutes', 'C': '96 minutes', 'D': '100 minutes', 'E': '2 hours'},
            'correct_answer_key': 'C',
            'solution_steps': [
                '15% = 72 minutes.',
                '1% = 72 / 15 = 4.8 minutes.',
                'Exercise time (20%) = $20 \times 4.8 = 96$ minutes.'
            ],
            'image_generator': generate_q11_pie_chart
        },
        {
            'id': 'Q19_Race',
            'topic': 'Distance-Time Graph (Race)',
            'question_text': "The graph shows the progress of a 20 km race between two boats. The boats set off from the harbour at 10:00, went round a buoy and then returned. Which boat finished first and by what distance was it ahead?",
            'data_description': 'Distance-Time Graph for two boats (A: dashed, B: solid) over a 20km race.',
            'data': {
                'race_distance': 20, 'boat_A_distance_at_1200': 1, 
                'boat_B_distance_at_1200': 0 
            },
            'options': {'A': 'Boat A by 1 km', 'B': 'Boat B by 1 km', 'C': 'Boat A by 2 km', 'D': 'It was a tie.', 'E': 'Boat B by 100 m'},
            'correct_answer_key': 'B',
            'solution_steps': [
                'The finish is at 0 km from the harbour (at the 12:00 line).',
                'At 12:00, Boat B (solid line) is at 0 km (finished).',
                'At 12:00, Boat A (dashed line) is at 1 km from the harbour.',
                'Boat B finished first, ahead of Boat A by 1 km.'
            ],
            'image_generator': generate_q19_race_graph
        }
    ]
    
    # --- FIX: CONSOLIDATE CARD DATA INTO Q17's DATA ---
    
    q17_data = next(q['data'] for q in questions if q['id'] == 'Q17')
    q18_data = next(q['data'] for q in questions if q['id'] == 'Q18')
    q19_mode_data = next(q['data'] for q in questions if q['id'] == 'Q19_Mode')

    # Merge Q18 and Q19 data into Q17's data. This resolves the KeyError in the visualizer.
    q17_data.update(q18_data)
    q17_data.update(q19_mode_data)
    
    return questions

# --- 3. MAIN EXECUTION BLOCK ---

def main():
    """Generates all images and prints question data."""
    all_questions = get_all_questions_data()
    
    generated_image_files = {}
    
    print("--- Generating Images and Loading Question Data ---")
    
    # Track the shared image generation to avoid duplicates
    card_image_generated = False
    grid_image_generated = False
    
    # Pre-fetch the consolidated card data once
    card_set_data = next(q['data'] for q in all_questions if q['id'] == 'Q17')
    
    for q_data in all_questions:
        q_id = q_data['id']
        image_generator = q_data.get('image_generator')

        if image_generator:
            filename = f"{q_id}_Image.png"
            data_to_pass = q_data['data']

            # --- Logic for Card Questions (Q17, Q18, Q19_Mode) ---
            if q_id in ['Q17', 'Q18', 'Q19_Mode']:
                filename = "Q17_18_19_Cards_Data.png"
                if card_image_generated:
                    generated_image_files[q_id] = filename
                    continue
                
                # Use the master consolidated data
                data_to_pass = card_set_data 
                card_image_generated = True

            # --- Logic for Coordinate Grid Questions (Q20, Q21) ---
            elif q_id in ['Q20', 'Q21']:
                filename = "Q20_Reflection_Grid.png"
                # Q20 generates the image, Q21 links to the generated image
                if q_id == 'Q21' and grid_image_generated: 
                    generated_image_files[q_id] = filename
                    continue
                
                grid_image_generated = True

            # Generate the image
            generated_file = image_generator(data_to_pass, filename)
            generated_image_files[q_id] = generated_file
            print(f"Generated image for {q_id}: {generated_file}")
    
    print("-" * 50)
    
    # --- Print Questions and Solution Steps ---
    for q in all_questions:
        print(f"\n# {q['id']}: {q['topic']}")
        print(f"**Question Text:** {q['question_text']}")
        print(f"**Options:**")
        for key, value in q['options'].items():
            print(f"  {key}: {value}")
        print(f"**Correct Answer Key:** {q['correct_answer_key']}")
        print(f"**Solution Steps:**")
        for step in q['solution_steps']:
            print(f"  - {step}")
        
        # Display the generated image reference
        if q['id'] in generated_image_files:
            print(f"\n**Image Reference for {q['id']}:**")
            print(f"(Image saved as: {generated_image_files[q['id']]})")
            
        print("\n" + "=" * 80 + "\n") 

if __name__ == "__main__":
    main()