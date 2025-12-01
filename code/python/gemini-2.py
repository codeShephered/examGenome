import json
import os

# --- Configuration ---
INPUT_FILE = '../../jsons/longDivFlashCard.json'
OUTPUT_FILE = '../../jsons/longDivFlashCard_extracted_data.json' # Optional: name for saving the extracted data

def extract_qa_data(input_filename):
    """
    Reads a JSON file, extracts 'question' and 'answer' fields,
    and returns a new list of dictionaries.
    """
    
    # 1. Check if the file exists
    if not os.path.exists(input_filename):
        print(f"Error: The input file '{input_filename}' was not found.")
        print("Please ensure your JSON data is correctly placed.")
        return []

    # 2. Load the JSON data
    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{input_filename}'. Check file integrity.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred during file reading: {e}")
        return []

    # Ensure the loaded data is a list (or iterable)
    if not isinstance(data, list):
        print("Warning: Expected a list of objects in the JSON file.")
        if isinstance(data, dict):
            # If it's a single dictionary, wrap it in a list
            data = [data]
        else:
            return []


    # 3. Process the data and extract fields
    extracted_data = []
    
    for item in data:
        # Use .get() to safely handle cases where 'details' might be present 
        # but 'question' or 'answer' might be missing (though unlikely in a structured file)
        
        question = item.get('question')
        answer = item.get('answer')
        
        # Only process if both key fields are present
        if question is not None and answer is not None:
            new_object = {
                "question": question,
                "answer": answer
            }
            extracted_data.append(new_object)
        else:
            print(f"Skipping object due to missing 'question' or 'answer': {item}")


    return extracted_data

# --- Example Usage ---
if __name__ == "__main__":
    # --- STEP 1: Create Dummy Input JSON Data for Demonstration ---
    dummy_input_data = [
        {
            "question": "What is the largest planet?",
            "answer": "Jupiter", 
            "details": "It is the fifth planet from the Sun."
        },
        {
            "question": "What is 7 times 8?", 
            "answer": "56", 
            "details": "Basic multiplication fact."
        },
        {
            "question": "Who painted the Mona Lisa?", 
            "answer": "Leonardo da Vinci", 
            "details": "Painted in the 16th century."
        }
    ]
    
    # Write dummy data to the input file
    #with open(INPUT_FILE, 'w', encoding='utf-8') as f:
     #   json.dump(dummy_input_data, f, indent=4)
        
    #print(f"Created dummy input file: {INPUT_FILE}\n")

    # --- STEP 2: Run the extractor ---
    final_structured_data = extract_qa_data(INPUT_FILE)

    # --- STEP 3: Print the final structured data ---
    if final_structured_data:
        #print("--- Final Extracted JSON Data Structure ---")
        # Use json.dumps to format the output string cleanly
        #print(json.dumps(final_structured_data, indent=4))
        
        # Optional: Save the extracted data to a new file
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_structured_data, f, indent=4)
        print(f"\nData also saved to {OUTPUT_FILE}")
