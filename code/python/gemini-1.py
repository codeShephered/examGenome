import json
import os
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

# --- Configuration ---
JSON_FILE = '../../jsons/longDivFlashCard_extracted_data.json'
OUTPUT_FILE = 'longDivFlashCard_verification.txt'

def generate_evaluation_prompt(filename):
    """
    Reads JSON data and generates a detailed prompt string for external evaluation.
    """
    if not os.path.exists(filename):
        print(f"Error: The file '{filename}' was not found.")
        return ""

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading/decoding JSON: {e}")
        return ""
    
    # 1. Create a formatted string dump of the entire data structure
    # This fulfills the requirement for '<data_structure_dump_from_json_file>'
    data_structure_dump = json.dumps(data, indent=4)
    
    # 2. Define the templates required in the prompt structure
    # Note: We use placeholders like '{{QUESTION_TEXT}}' here, as the final output 
    # must define the templates for the recipient.
    # SUCCESS_TEMPLATE = (
    #     "Question: {question}\n"
    #     "Status: Success\n"
    # )

    # ERROR_TEMPLATE = (
    #     "Question: {question}\n"
    #     "Status: Error\n"
    #     "Explanation: <provide detailed explanation on the error>\n"
    # )

    # 3. Assemble the main instruction block
    # This is the single, overarching prompt instruction.
    main_prompt_instruction = (
        f"--- EVALUATION INSTRUCTIONS ---\n\n"
        f"If the answer for each object in the given json data structure\n"
        f"'{data_structure_dump}'\n"
        f"is correct to the corresponding question in the Json object, "
        f"print the SUCCESS_TEMPLATE below. If the answer is incorrect, print the ERROR_TEMPLATE.\n\n"
        
        f"SUCCESS_TEMPLATE:\n"
        f"Question: {{question}}\n"
        f"Status: Success\n\n"
        
        f"ERROR_TEMPLATE:\n"
        f"Question: {{question}}\n"
        f"Status: Error\n"
        f"Explanation: <provide detailed explanation on the error>\n\n"
        
        f"--- START EVALUATION ---\n"
    )
    
    # 4. Generate the specific evaluation instruction for each item
    # This instructs the AI to evaluate each pair from the JSON data.
    # evaluation_blocks = []
    
    # for item in data:
    #     question = item.get('question', 'QUESTION_MISSING')
    #     answer = item.get('answer', 'ANSWER_MISSING')
        
    #     # This provides the necessary context for the AI to perform the check.
    #     # It forces the AI to check the given answer against the given question.
    #     evaluation_instruction = (
    #         f"EVALUATE ITEM:\n"
    #         f"Q: {question}\n"
    #         f"A: {answer}\n"
    #         f"--- RESULT ---\n"
    #     )
    #     evaluation_blocks.append(evaluation_instruction)

    # # Combine everything into the final prompt string
    # final_prompt = main_prompt_instruction + "\n".join(evaluation_blocks)

    genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

    model = genai.GenerativeModel('gemini-2.5-flash') # Choose an appropriate model
    #model = genai.GenerativeModel('gemini-1.5-flash') # Choose an appropriate model

    #prompt = "If the answer(Divide the leftmost digit(s) of the dividend by the divisor.) for the question(Divide the leftmost digit(s) of the \
    #dividend by the divisor.) reply to this prompt as yes or provide the correct answer with explanation"

    response = model.generate_content(main_prompt_instruction)

    #print(response.text)
    
    return(response.text)

# --- Example Usage ---
if __name__ == "__main__":
    final_prompt_string = generate_evaluation_prompt(JSON_FILE)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as s:
        print(final_prompt_string, file=s)

    # --- STEP 1: Create Dummy Input JSON Data ---
    # dummy_input_data = [
    #     {
    #         "question": "What is 10 + 5?",
    #         "answer": "15", 
    #         "details": "Correct."
    #     },
    #     {
    #         "question": "Which planet is closest to the Sun?", 
    #         "answer": "Mars", 
    #         "details": "Incorrect, should be Mercury."
    #     }
    # ]
    
    # with open(JSON_FILE, 'w', encoding='utf-8') as f:
    #     json.dump(dummy_input_data, f, indent=4)
        
    # print(f"Created input file: {JSON_FILE}\n")

    # --- STEP 2: Generate and print the final prompt ---
    # final_prompt_string = generate_evaluation_prompt(JSON_FILE)
    
    # if final_prompt_string:
    #     print("--- GENERATED AI PROMPT ---")
    #     with open(OUTPUT_FILE, 'w', encoding='utf-8') as s:
    #         print(final_prompt_string, file=s)

    
