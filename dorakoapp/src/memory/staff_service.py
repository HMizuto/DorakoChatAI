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
    
def upsert_staff(line_user_id: str, display_name: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
                INSERT INTO staff (line_user_id, display_name)
                VALUES (%s, %s)
                ON CONFLICT (line_user_id)
                DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    updated_at = NOW()
    """,(line_user_id, display_name))
    conn.commit()
    conn.close()