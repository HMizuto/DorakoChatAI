import requests
from linebot import LineBotApi
from linebot.models import TextSendMessage

from core.config import Config

LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"


class LineMessenger:
    def __init__(self, config: Config):
        self._api   = LineBotApi(config.line_channel_access_token)
        self._token = config.line_channel_access_token

    def reply_text(self, reply_token: str, text: str) -> None:
        self._api.reply_message(reply_token, TextSendMessage(text=text))

    def reply_with_mention(self, reply_token: str, executives: list[dict], body_text: str) -> None:
        """
        幹部をメッセージ先頭で proper mention（青文字・通知あり）してから本文を送信する。
        textV2 + substitution 方式を使用。
        """
        substitution     = {}
        placeholder_parts = []

        for i, exec_user in enumerate(executives):
            key = f"mention{i}"   # ^[a-zA-Z0-9_]{1,20}$ に準拠
            substitution[key] = {
                "type": "mention",
                "mentionee": {
                    "type":   "user",
                    "userId": exec_user["line_user_id"],
                },
            }
            placeholder_parts.append(f"{{{key}}}")

        mention_line = " ".join(placeholder_parts)
        full_text    = f"{mention_line}\n{body_text}"

        payload = {
            "replyToken": reply_token,
            "messages": [
                {
                    "type":         "textV2",
                    "text":         full_text,
                    "substitution": substitution,
                }
            ],
        }

        requests.post(
            LINE_REPLY_URL,
            headers={
                "Content-Type":  "application/json",
                "Authorization": f"Bearer {self._token}",
            },
            json=payload,
        )
