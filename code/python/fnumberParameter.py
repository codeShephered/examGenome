import os
import json

# The dictionary defining the key prefixes and their corresponding values
fileDict = {"two": 2,
"three": 3,
"four": 4,
"five": 5,
"six": 6,
"seven": 7,
"nine": 9,
"ten": 10,
"eleven": 11,
"twelve": 12,
"thirteen": 13,
"fourteen": 14,
"fifteen": 15,
"sixteen": 16,
"eighteen": 18,
"nineteen": 19,
"twenty": 20,
"twentyone": 21,
"twentytwo": 22,
"twentythree": 23,
"twentyfour": 24,
"twentysix": 26,
"twentyseven": 27,
"twentyeight": 28,
"twentynine": 29,
"thirty": 30,
"thirtyone": 31,
"thirtytwo": 32,
"thirtythree": 33,
"thirtyfour": 34,
"thirtyfive": 35,
"thirtysix": 36,
"thirtyeight": 38,
"thirtynine": 39,
"forty": 40,
"fortyone": 41,
"fortytwo": 42,
"fortythree": 43,
"fortysix": 46,
"fortyseven": 47,
"fortynine": 49,
"fifty": 50,
"fiftyone": 51,
"fiftytwo": 52,
"fiftythree": 53,
"fiftyfour": 54,
"fiftyfive": 55,
"fiftyseven": 57,
"fiftynine": 59,
"sixty": 60,
"sixtyone": 61,
"sixtyfour": 64,
"sixtyfive": 65,
"sixtysix": 66,
"sixtyseven": 67,
"sixtyeight": 68,
"sixtynine": 69,
"seventy": 70,
"seventyone": 71,
"seventytwo": 72,
"seventyfour": 74,
"seventyfive": 75,
"seventysix": 76,
"seventyseven": 77,
"seventyeight": 78,
"seventynine": 79,
"eighty": 80,
"eightyone": 81,
"eightytwo": 82,
"eightythree": 83,
"eightyfour": 84,
"eightyseven": 87,
"eightyeight": 88,
"eightynine": 89,
"ninety": 90,
"ninetyone": 91,
"ninetytwo": 92,
"ninetythree": 93,
"ninetyfour": 94,
"ninetyfive": 95,
"ninetyeight": 98,
"ninetynine": 99,
"onehundred": 100,
"onehundredandone": 101,
"onehundredandtwo": 102,
"onehundredandthree": 103,
"onehundredandfive": 105,
"onehundredandsix": 106,
"onehundredandeight": 108,
"onehundredandnine": 109,
"onehundredandten": 110,
"onehundredandeleven": 111,
"onehundredandtwelve": 112,
"onehundredandthirteen": 113,
"onehundredandfourteen": 114,
"onehundredandfifteen": 115,
"onehundredandeighteen": 118,
"onehundredandtwenty": 120,
"onehundredandtwentyone": 121,
"onehundredandtwentytwo": 122,
"onehundredandtwentythree": 123,
"onehundredandtwentyfour": 124,
"onehundredandtwentysix": 126,
"onehundredandthirty": 130,
"onehundredandthirtyone": 131,
"onehundredandthirtytwo": 132,
"onehundredandthirtythree": 133,
"onehundredandthirtyfour": 134
}

# The folder containing the JSON files
FOLDER_PATH = "qBaseJson"

def update_json_files(folder_path, update_map):
    """
    Parses and updates JSON files in a folder based on a key prefix map.
    It inserts "fnumber": <value> into the root of the JSON object.
    """
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' not found.")
        return

    print(f"Starting file update in '{folder_path}'...")
    
    # Iterate through all files in the specified directory
    for filename in os.listdir(folder_path):
        # Only process files ending with .json
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            
            # Check for a matching prefix in fileDict
            matching_key = None
            for key_prefix in update_map:
                # Check if the filename starts with the key_prefix followed by an underscore
                if filename.startswith(f"{key_prefix}_"):
                    matching_key = key_prefix
                    break
            
            if matching_key:
                # The value to insert into the JSON
                new_fnumber = update_map[matching_key]
                
                try:
                    # 1. Load the JSON file
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    # 2. Modify the Python dictionary
                    # Add the new key-value pair as requested
                    data["fnumber"] = new_fnumber
                    
                    # 3. Write the modified dictionary back to the file
                    with open(file_path, 'w') as f:
                        # Use indent=4 for clean, readable output
                        json.dump(data, f, indent=4)
                        
                    print(f"✅ Updated '{filename}' with 'fnumber': {new_fnumber}")
                
                except json.JSONDecodeError:
                    print(f"❌ Error decoding JSON in file: {filename}. Skipping.")
                except Exception as e:
                    print(f"❌ An error occurred while processing {filename}: {e}. Skipping.")
            else:
                print(f"⏩ Skipping '{filename}': No matching prefix found.")

# Execute the update function
update_json_files(FOLDER_PATH, fileDict)

# Example of what would happen inside the file:
# Original JSON: {"data": "test"}
# New JSON:
# {
#     "fnumber": 2,
#     "data": "test"
# }