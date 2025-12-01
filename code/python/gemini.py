import os
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()
# The SDK automatically looks for the GEMINI_API_KEY or GOOGLE_API_KEY
# environment variable.
# You can also configure it manually:
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

model = genai.GenerativeModel('gemini-2.5-flash') # Choose an appropriate model
#model = genai.GenerativeModel('gemini-1.5-flash') # Choose an appropriate model

prompt = "If the answer(Divide the leftmost digit(s) of the dividend by the divisor.) for the question(Divide the leftmost digit(s) of the \
dividend by the divisor.) reply to this prompt as yes or provide the correct answer with explanation"

response = model.generate_content(prompt)

print(response.text)

