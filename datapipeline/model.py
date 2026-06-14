import requests

url = "http://127.0.0.1:1234/v1/chat/completions"

payload = {
    "model": "qwen2.5-vl-3b-instruct",
    "messages": [
        {
            "role": "user",
            "content": "Hi"
        }
    ]
}

response = requests.post(url, json=payload)

print("Status:", response.status_code)
print(response.text)