from pathlib import Path

from openai import OpenAI

from core.config import Config
from repositories.conversation_repository import ConversationRepository

_BASE_DIR    = Path(__file__).resolve().parents[1]
_PROMPT_PATH = _BASE_DIR / "docs" / "prompts" / "base_system_prompt.txt"

with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
    _BASE_PROMPT = f.read()


class ChatService:
    def __init__(self, conv_repo: ConversationRepository, config: Config):
        self._conv_repo = conv_repo
        self._client    = OpenAI(api_key=config.openai_api_key)
        self._model     = config.openai_model_chat

    def chat(self, user_id: str, user_text: str) -> str:
        history = self._conv_repo.get_recent(user_id)

        messages = [
            {"role": "system", "content": [{"type": "input_text", "text": _BASE_PROMPT}]},
            *history,
            {"role": "user", "content": [{"type": "input_text", "text": user_text}]},
        ]

        response = self._client.responses.create(
            model=self._model,
            input=messages,
            temperature=0.7,
        )
        return response.output_text
