from core.database import Database


class EscalationRepository:
    def __init__(self, db: Database):
        self._db = db

    def save(self, line_user_id: str, display_name: str, message: str,
             reason: str, group_id: str | None = None) -> None:
        """
        reason: 'RAG_MISS' | 'CONSULTATION' | 'REPORT'
        """
        with self._db.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO escalations (line_user_id, display_name, message, reason, group_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (line_user_id, display_name, message, reason, group_id))

    def get_open_in_group(self, group_id: str) -> dict | None:
        """グループ内の最新 OPEN エスカレーションを返す。なければ None。"""
        with self._db.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, line_user_id, display_name, message, reason, created_at
                FROM escalations
                WHERE group_id = %s AND status = 'OPEN'
                ORDER BY created_at DESC
                LIMIT 1
            """, (group_id,))
            row = cur.fetchone()
        if not row:
            return None
        return {
            "id":           row[0],
            "line_user_id": row[1],
            "display_name": row[2],
            "message":      row[3],
            "reason":       row[4],
            "created_at":   row[5],
        }

    def resolve(self, escalation_id: int, resolved_by: str, executive_reply: str) -> None:
        """エスカレーションを解決済みにする。"""
        with self._db.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE escalations
                SET status          = 'RESOLVED',
                    resolved_at     = NOW(),
                    resolved_by     = %s,
                    executive_reply = %s
                WHERE id = %s
            """, (resolved_by, executive_reply, escalation_id))
