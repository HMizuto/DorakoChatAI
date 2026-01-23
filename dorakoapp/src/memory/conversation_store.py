import psycopg2
import config as config

class ConversationService:

    @staticmethod
    def get_conn():
        return psycopg2.connect(
            host=config.PG_HOST,
            port=config.PG_PORT,
            dbname=config.PG_DB,
            user=config.PG_USER,
            password=config.PG_PASSWORD
        )

    @staticmethod
    def save_message(user_id: str, role: str, message: str):
        conn = ConversationService.get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO conversation_logs (line_user_id, role, message)
            VALUES (%s, %s, %s)
        """, (user_id, role, message))
        conn.commit()
        conn.close()

    @staticmethod
    def get_recent_messages(user_id: str, limit: int = 10):
        conn = ConversationService.get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT role, message
            FROM conversation_logs
            WHERE line_user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (user_id, limit))

        rows = cur.fetchall()
        conn.close()

        history = []
        for role, message in reversed(rows):
            if role == "user":
                history.append({
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": message}
                    ]
                })
            elif role == "assistant":
                history.append({
                    "role": "assistant",
                    "content": [
                        {"type": "output_text", "text": message}
                    ]
                })
            # system を保存していないなら else は不要

        return history
