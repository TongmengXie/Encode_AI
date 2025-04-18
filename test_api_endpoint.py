import requests
import json

# Test the embedding API endpoint
api_url = "http://localhost:5000/api/embedding"

print(f"Testing API endpoint: {api_url}")
try:
    response = requests.get(api_url)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("Response JSON:")
        print(json.dumps(data, indent=2))
    else:
        print("Error Response:")
        try:
            data = response.json()
            print(json.dumps(data, indent=2))
        except:
            print(response.text)
            
except Exception as e:
    print(f"Error: {str(e)}") 