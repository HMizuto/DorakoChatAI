import pandas as pd
from openai import OpenAI

from core.config import Config
from repositories.qa_repository import QARepository


class QAUpdater:
    def __init__(self, qa_repo: QARepository, config: Config):
        self._qa_repo = qa_repo
        self._client  = OpenAI(api_key=config.openai_api_key)
        self._model   = config.openai_model_embed
        self._url     = config.spreadsheet_url

    def run(self) -> dict:
        """
        スプレッドシートからQAを読み込んでUpsertする。

        Returns:
            {"success": bool, "inserted": int, "updated": int, "skipped": int,
             "inserted_ids": list, "updated_ids": list, "error": str | None}
        """
        result = {
            "success":      False,
            "inserted":     0,
            "updated":      0,
            "skipped":      0,
            "inserted_ids": [],
            "updated_ids":  [],
            "error":        None,
        }

        try:
            df = pd.read_csv(self._url)
        except Exception as e:
            result["error"] = f"スプレッドシートの読み込みに失敗しました: {e}"
            return result

        try:
            existing = self._qa_repo.get_existing()

            for _, row in df.iterrows():
                qa_id      = int(row["qa_id"])
                category   = row.get("category")
                question   = row["question"]
                answer     = row["answer"]
                updated_at = row["updated_at"]

                if qa_id in existing:
                    if str(existing[qa_id]) == str(updated_at):
                        result["skipped"] += 1
                        continue
                    embedding = self._embed(f"Q: {question}\nA: {answer}")
                    self._qa_repo.update(qa_id, category, question, answer, embedding, updated_at)
                    result["updated"] += 1
                    result["updated_ids"].append(qa_id)
                else:
                    embedding = self._embed(f"Q: {question}\nA: {answer}")
                    self._qa_repo.insert(qa_id, category, question, answer, embedding, updated_at)
                    result["inserted"] += 1
                    result["inserted_ids"].append(qa_id)

            result["success"] = True

        except Exception as e:
            result["error"] = f"DB処理中にエラーが発生しました: {e}"

        return result

    def _embed(self, text: str) -> list:
        res = self._client.embeddings.create(model=self._model, input=text)
        return res.data[0].embedding
