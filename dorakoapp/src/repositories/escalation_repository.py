from core.database import Database


class EscalationRepository:
    def __init__(self, db: Database):
        self._db = db

    def save(self, line_user_id: str, display_name: str, message: str, reason: str) -> None:
        """
        reason: 'CONSULTATION' | 'REPORT' | 'RAG_MISS'
        """
        with self._db.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO escalations (line_user_id, display_name, message, reason)
                VALUES (%s, %s, %s, %s)
            """, (line_user_id, display_name, message, reason))
