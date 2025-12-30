import json
import os
import google.generativeai as genai
import time
from dotenv import load_dotenv
load_dotenv()



# --- Configuration ---
JSON_FILE = '../../jsons/year456/src/y6_Ratio_proportion_extracted_data.json'
OUTPUT_FILE = '../../jsons/year456/verif/y6_Ratio_proportion_verification.txt'
# Set the batch size as required
BATCH_SIZE = 100

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
    #data_structure_dump = json.dumps(data, indent=4)
    
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
    all_responses = []
    num_objects = len(data)
    genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

    model = genai.GenerativeModel('gemini-2.5-flash') # Choose an appropriate model

    # Iterate through the data in batches of BATCH_SIZE (100)
    for i in range(0, num_objects, BATCH_SIZE):
        batch = data[i:i + BATCH_SIZE]
        batch_number = (i // BATCH_SIZE) + 1
        
        print(f"--- Processing Batch {batch_number}: Objects {i} to {i + len(batch) - 1} ---")
        
        # 1. Create a formatted string dump of only the current batch
        # This becomes the '<data_structure_dump_from_json_file>' for this prompt
        batch_data_dump = json.dumps(batch, indent=4)
        
        # 2. Assemble the main instruction block for the current batch

        main_prompt_instruction = (
            f"--- EVALUATION INSTRUCTIONS (Batch {batch_number}) ---\n\n"
            f"If the answer for each object among the options in the given json data structure\n"
            f"'{batch_data_dump}'\n"
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
    
        # 3. Call the model with the batch-specific prompt
        #if batch_number > 3:
        try:
            response = model.generate_content(main_prompt_instruction)
            all_responses.append(response.text)
            print(f"Successfully received response for Batch {batch_number}.")
        except Exception as e:
            print(f"Error generating content for Batch {batch_number}: {e}")
            all_responses.append(f"ERROR: Could not process Batch {batch_number}.")
            time.sleep(300)
        #else:
        #    continue
    
    #model = genai.GenerativeModel('gemini-1.5-flash') # Choose an appropriate model

    #prompt = "If the answer(Divide the leftmost digit(s) of the dividend by the divisor.) for the question(Divide the leftmost digit(s) of the \
    #dividend by the divisor.) reply to this prompt as yes or provide the correct answer with explanation"

    #response = model.generate_content(main_prompt_instruction)

    #print(response.text)
    
    return(all_responses)

# --- Example Usage ---
if __name__ == "__main__":
    final_prompt_string = generate_evaluation_prompt(JSON_FILE)
    #json_output = json.dumps(final_prompt_string, indent=2)
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

    
