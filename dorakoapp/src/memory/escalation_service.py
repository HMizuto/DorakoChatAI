# memory/escalation_service.py
import psycopg2
import config

def get_conn():
    return psycopg2.connect(
        host=config.PG_HOST,
        port=config.PG_PORT,
        dbname=config.PG_DB,
        user=config.PG_USER,
        password=config.PG_PASSWORD
    )

def save_escalation(line_user_id: str, display_name: str, message: str, reason: str):
    """
    reason: 'CONSULTATION' / 'REPORT' / 'RAG_MISS'
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO escalations (line_user_id, display_name, message, reason)
        VALUES (%s, %s, %s, %s)
    """, (line_user_id, display_name, message, reason))
    conn.commit()
    conn.close()