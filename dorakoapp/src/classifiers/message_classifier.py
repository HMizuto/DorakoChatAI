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

- QUESTION   : 業務手順・給与・契約・申請方法など、具体的な情報を求めている
- CONSULTATION: 退職・欠勤・職場の悩み・人間関係など、判断や助言が必要な相談
- CHAT       : 挨拶・雑談など業務に関係ない会話
- REPORT     : 「〜しました」「〜です」など、情報を伝えることが目的の報告・連絡
- OTHER      : 上記に当てはまらないもの

迷った場合はQUESTIONを優先してください。
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
