from pathlib import Path

from openai import OpenAI

from core.config import Config
from repositories.qa_repository import QARepository
from repositories.conversation_repository import ConversationRepository

_BASE_DIR   = Path(__file__).resolve().parents[1]
_PROMPT_PATH = _BASE_DIR / "docs" / "prompts" / "base_system_prompt.txt"

with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
    _BASE_PROMPT = f.read()


class RAGService:
    def __init__(self, qa_repo: QARepository, conv_repo: ConversationRepository, config: Config):
        self._qa_repo   = qa_repo
        self._conv_repo = conv_repo
        self._client    = OpenAI(api_key=config.openai_api_key)
        self._model     = config.openai_model_chat
        self._embed_model = config.openai_model_embed

    def answer(self, user_id: str, question: str) -> tuple[str | None, bool]:
        """
        Returns:
            (answer, True)  : RAGヒット
            (None,   False) : RAGミス → 呼び出し元でエスカレーション処理
        """
        self._conv_repo.save(user_id, "user", question)

        history = self._conv_repo.get_recent(user_id, limit=8)
        embedding = self._embed(question)
        chunks    = self._qa_repo.search(embedding)

        if not chunks:
            return None, False

        context_text = "\n\n".join(
            [f"Q: {c['question']}\nA: {c['answer']}" for c in chunks]
        )

        messages = [
            {"role": "system", "content": [{"type": "input_text", "text": _BASE_PROMPT}]},
            *history,
            {
                "role": "system",
                "content": [{
                    "type": "input_text",
                    "text": f"""以下の知識ベースに答えがあります。
この内容だけを根拠にして回答してください。
知識ベースに書かれていないことは絶対に補足・推測しないでください。

【知識ベース】
{context_text}

【質問】
{question}""",
                }],
            },
            {"role": "user", "content": [{"type": "input_text", "text": question}]},
        ]

        response = self._client.responses.create(
            model=self._model,
            input=messages,
            temperature=0.2,
        )
        answer = response.output_text

        self._conv_repo.save(user_id, "assistant", answer)
        return answer, True

    def _embed(self, text: str) -> list:
        res = self._client.embeddings.create(model=self._embed_model, input=text)
        return res.data[0].embedding
