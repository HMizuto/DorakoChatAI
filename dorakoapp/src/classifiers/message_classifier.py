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
                        "text": """次のユーザー入力を以下の分類のどれか1つに分類してください。
分類名のみを返してください。それ以外の文字は一切含めないでください。

- QUESTION   : 業務・給与・契約などに関する質問
- CONSULTATION: 悩み・トラブル・退職・欠勤などの相談
- CHAT       : 挨拶・雑談など業務に関係ない会話
- REPORT     : 業務報告・連絡・確認事項の共有
- OTHER      : 上記に当てはまらないもの
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
