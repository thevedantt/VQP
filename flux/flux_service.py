import requests
import base64

class FluxService:

    def __init__(self):
        self.api_key = ""

        self.url = (
            "https://ai.api.nvidia.com/v1/genai/"
            "black-forest-labs/flux.1-schnell"
        )

    def generate_image(self, prompt: str):

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

        payload = {
            "prompt": prompt,
            "width": 1024,
            "height": 1024,
            "seed": 0,
            "steps": 4
        }

        response = requests.post(
            self.url,
            headers=headers,
            json=payload,
            timeout=120
        )

        response.raise_for_status()

        img_b64 = response.json()["artifacts"][0]["base64"]

        with open("output1.jpg", "wb") as f:
            f.write(base64.b64decode(img_b64))

        print("saved")
