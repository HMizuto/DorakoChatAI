from core.database import Database


class ConversationRepository:
    def __init__(self, db: Database):
        self._db = db

    def save(self, user_id: str, role: str, message: str) -> None:
        with self._db.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO conversation_logs (line_user_id, role, message)
                VALUES (%s, %s, %s)
            """, (user_id, role, message))

    def get_recent(self, user_id: str, limit: int = 10) -> list[dict]:
        with self._db.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT role, message
                FROM conversation_logs
                WHERE line_user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (user_id, limit))
            rows = cur.fetchall()

        history = []
        for role, message in reversed(rows):
            if role == "user":
                history.append({
                    "role": "user",
                    "content": [{"type": "input_text", "text": message}],
                })
            elif role == "assistant":
                history.append({
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": message}],
                })
        return history
