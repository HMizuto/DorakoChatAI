from core.database import Database


class QARepository:
    def __init__(self, db: Database):
        self._db = db

    def search(self, embedding: list, top_k: int = 1, threshold: float = 0.25) -> list[dict]:
        with self._db.connect(vector=True) as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT question, answer, embedding <=> %s::vector AS distance
                FROM qa_vectors
                ORDER BY distance
                LIMIT %s
            """, (embedding, top_k))
            rows = cur.fetchall()
        return [
            {"question": r[0], "answer": r[1], "distance": r[2]}
            for r in rows if r[2] <= threshold
        ]

    def get_existing(self) -> dict:
        """Returns {id: created_at} for all existing QA entries."""
        with self._db.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, created_at FROM qa_vectors")
            rows = cur.fetchall()
        return {row[0]: row[1] for row in rows}

    def insert(self, qa_id: int, category, question: str, answer: str,
               embedding: list, updated_at: str) -> None:
        with self._db.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO qa_vectors (id, category, question, answer, embedding, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (qa_id, category, question, answer, embedding, updated_at))

    def update(self, qa_id: int, category, question: str, answer: str,
               embedding: list, updated_at: str) -> None:
        with self._db.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE qa_vectors
                SET category=%s, question=%s, answer=%s, embedding=%s, created_at=%s
                WHERE id=%s
            """, (category, question, answer, embedding, updated_at, qa_id))
