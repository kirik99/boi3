import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")

url = "https://api.deepseek.com/v1/embeddings"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
data = {
    "model": "deepseek-embedding",
    "input": "test text"
}

resp = requests.post(url, headers=headers, json=data)
print(resp.status_code)
print(resp.text)
