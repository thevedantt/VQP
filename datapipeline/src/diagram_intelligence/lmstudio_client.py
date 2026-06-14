import requests
from typing import Optional

from utils.logger import logger

class LMStudioClient:
    """
    Communicates with local LM Studio completion API for diagram analysis.
    """

    def __init__(self, endpoint: str = "http://127.0.0.1:1234/v1/chat/completions", timeout: int = 60):
        self.endpoint = endpoint
        self.timeout = timeout

    def call_llm(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        payload = {
            "model": "qwen2.5-vl-3b-instruct",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1
        }
        try:
            response = requests.post(self.endpoint, json=payload, timeout=self.timeout)
            if response.status_code == 200:
                res_json = response.json()
                return res_json["choices"][0]["message"]["content"]
            else:
                logger.error(f"LM Studio error {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Failed to query LM Studio: {str(e)}")
        return None
