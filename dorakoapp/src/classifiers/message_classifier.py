# services/classifier_service.py
from openai import OpenAI
import config

class ClassifierService:

    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)

    def classify(self, text: str) -> str:
        res = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "system",
                    "content": [{
                        "type": "input_text",
                        "text": """次のユーザー入力を分類してください。
以下のどれか1つだけを返してください。

- QUESTION
- CONSULTATION
- CHAT
- OTHER
"""
                    }]
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": text}]
                }
            ],
            temperature=0
        )
        return res.output_text.strip()
