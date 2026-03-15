from core.database import Database


class ConversationRepository:
    def __init__(self, db: Database):
        self._db = db

    # --------------------------------------------------
    #  1on1 AI 会話履歴 (RAGService / ChatService 用)
    # --------------------------------------------------

    def save(self, user_id: str, role: str, message: str) -> None:
        """1on1 AI 会話ログを保存する。group_id は NULL。"""
        with self._db.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO conversation_logs (line_user_id, role, message)
                VALUES (%s, %s, %s)
            """, (user_id, role, message))

    def get_recent(self, user_id: str, limit: int = 10) -> list[dict]:
        """1on1 AI 会話履歴を取得する（group_id IS NULL のみ）。"""
        with self._db.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT role, message
                FROM conversation_logs
                WHERE line_user_id = %s AND group_id IS NULL
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

    # --------------------------------------------------
    #  グループ会話記録 (ログ保存用)
    # --------------------------------------------------

    def save_group_message(self, group_id: str, user_id: str,
                           display_name: str, role: str, message: str) -> None:
        """
        グループ会話を記録する。
        role: 'staff' | 'executive'
        """
        with self._db.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO conversation_logs
                    (line_user_id, role, message, group_id, display_name)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, role, message, group_id, display_name))

    def get_recent_group(self, group_id: str, limit: int = 15) -> list[dict]:
        """
        グループの直近会話を時系列順（古い→新しい）で返す。
        継続判定 AI に渡すため display_name と created_at も含む。
        """
        with self._db.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT role, display_name, message, created_at
                FROM conversation_logs
                WHERE group_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (group_id, limit))
            rows = cur.fetchall()

        return [
            {
                "role":         row[0],
                "display_name": row[1],
                "message":      row[2],
                "created_at":   row[3],
            }
            for row in reversed(rows)   # 古い順に並べ直す
        ]
