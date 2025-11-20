import requests 
api_url = "https://www.wolframcloud.com/obj/raghuinfobits/animal-hay-cost-api?numQuestions=10&difficulty=easy" # Example API endpoint 
response = requests.get(api_url) 
data = response.json() 
print("API Response Data:") 
print(data)