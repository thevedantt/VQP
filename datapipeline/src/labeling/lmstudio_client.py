import json
import time
import requests
from typing import Dict, Any, Optional

from utils.logger import logger

class LMStudioClient:
    """
    Client to communicate with the local LM Studio server running Qwen2.5 VL 3B Instruct.
    """

    def __init__(self, endpoint: str = "http://127.0.0.1:1234/v1/chat/completions", timeout: int = 60):
        self.endpoint = endpoint
        self.timeout = timeout

    def call_llm(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> Optional[str]:
        """
        Sends request to LM Studio and returns completion response.
        Includes retries and exponential backoff.
        """
        payload = {
            "model": "qwen2.5-vl-3b-instruct",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1
        }
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"LLM API Call - Attempt {attempt}/{max_retries}")
                response = requests.post(self.endpoint, json=payload, timeout=self.timeout)
                
                if response.status_code == 200:
                    res_json = response.json()
                    content = res_json["choices"][0]["message"]["content"]
                    return content
                else:
                    logger.error(f"LM Studio returned status code {response.status_code}: {response.text}")
                    if attempt < max_retries:
                        time.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"Unexpected error calling LM Studio (Attempt {attempt}): {str(e)}")
                if attempt < max_retries:
                    time.sleep(2 ** attempt)

        return None
