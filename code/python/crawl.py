import requests
import json
import zipfile
import os
import re

# === CONFIG ===

TOTAL_REQUESTS = 1000
OUTPUT_DIR = "api_outputs_remaining"


base_url = [
"https://www.wolframcloud.com/obj/raghu0891/fiftythree?n=1000&difficulty=easy&topic=Product of Prime Factors"
]




#os._exit(1) # Exit immediately with status 1
# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_json(url):
    """Fetch data from API (can customize with query params like ?page=idx).
       Returns only the first entry of the JSON output."""
    try:
        resp = requests.get(f"{url}", timeout=60)
        resp.raise_for_status()
        data = resp.json()

        # If JSON is a list → return first item
        if isinstance(data, list) and len(data) > 0:
            return data

        # If JSON is a dict → return first key:value pair as {key: value}
        elif isinstance(data, dict) and len(data) > 0:
            first_key = next(iter(data))
            return {first_key: data[first_key]}

        else:
            print(f"⚠️ No valid data found at link {url}")
            return None

    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
        return None


def main():
    print("⚡ Fetching API data...")
    
    for item in base_url:
        filenameRegex = re.compile(r'https://www.wolframcloud.com/obj/raghu0891/([^?]*).*')
        #print(item)
        mo = filenameRegex.search(item)
        #print(mo)
        FILE_NAME = mo.group(1)
        difficultyRegex = re.compile(r'https://www.wolframcloud.com/obj/raghu0891/.*?difficulty=(.*)$')
        difficultymo = difficultyRegex.search(item)
        DIFFICULTY = difficultymo.group(1)
        topicRegex = re.compile(r'https://www.wolframcloud.com/obj/raghu0891/.*?topic=(.*)$')
        topicmo = topicRegex.search(item)
        TOPIC = topicmo.group(1)
        FIRST_FILE = FILE_NAME+"_"+DIFFICULTY+"_"+TOPIC+"_first_response.json"
        ARCHIVE_FILE = FILE_NAME+"_"+DIFFICULTY+"_"+TOPIC+"_remaining_responses.zip"
        
        #FIRST_FILE = FILE_NAME+"_"+DIFFICULTY+"_first_response.json"
        #ARCHIVE_FILE = FILE_NAME+"_"+DIFFICULTY+"_remaining_responses.zip"

        #FIRST_FILE = "first_response"+"_"+DIFFICULTY+"_"+FILE_NAME+".json"
        #ARCHIVE_FILE = "remaining_responses"+"_"+DIFFICULTY+"_"+FILE_NAME+".zip"
        
        print("FILE NAME: "+FILE_NAME)
        print("FIRST FILE: "+FIRST_FILE)
        print("ARCHIVE NAME: "+ARCHIVE_FILE)
        data = fetch_json(item) 
        
        #os._exit(1) # Exit immediately with status 1
        if data:
            with open(os.path.join(OUTPUT_DIR, FIRST_FILE), "w") as f:
                json.dump(data[0], f, indent=4)
            print(f"✅ First response saved as {FIRST_FILE}")
        
        # Save remaining 999 into individual files
        # Collect all remaining JSON entries into a single list
        #remaining_data = []

        #for i in range(2, TOTAL_REQUESTS + 1):
        #    data = fetch_json(item, i)
        #    if data:
        #        remaining_data.append(data)

        # Save into one JSON file
        combined_file = os.path.join(OUTPUT_DIR, "remaining_responses.json")
        with open(combined_file, "w") as f:
            #json.dump(remaining_data, f, indent=4)
            json.dump(data[1:], f, indent=4)

        # Archive it as zip
        with zipfile.ZipFile(os.path.join(OUTPUT_DIR, ARCHIVE_FILE), "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(combined_file, arcname="remaining_responses.json")

        # Optionally delete the plain JSON after zipping
        os.remove(combined_file)
        print("----------------------------------------------------------------")
        print(f"✅ Remaining {TOTAL_REQUESTS-1} responses saved in archive {ARCHIVE_FILE}")


if __name__ == "__main__":
    main()
