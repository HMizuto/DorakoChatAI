from core.database import Database


class Permission:
    SYSADMIN = "システム管理者"
    INTERNAL = "社内"
    STAFF    = "スタッフ"


class UserRepository:
    def __init__(self, db: Database):
        self._db = db

    def get(self, line_user_id: str) -> dict | None:
        with self._db.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT line_user_id, display_name, permission_level, group_id, is_active
                FROM users
                WHERE line_user_id = %s
            """, (line_user_id,))
            row = cur.fetchone()
        if not row:
            return None
        return {
            "line_user_id":     row[0],
            "display_name":     row[1],
            "permission_level": row[2],
            "group_id":         row[3],
            "is_active":        row[4],
        }

    def is_internal(self, line_user_id: str) -> bool:
        user = self.get(line_user_id)
        if not user:
            return False
        return user["permission_level"] in (Permission.SYSADMIN, Permission.INTERNAL)

    def get_executives_in_group(self, group_id: str) -> list[dict]:
        with self._db.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT line_user_id, display_name
                FROM users
                WHERE group_id = %s
                  AND permission_level IN (%s, %s)
                  AND is_active = TRUE
            """, (group_id, Permission.SYSADMIN, Permission.INTERNAL))
            rows = cur.fetchall()
        return [{"line_user_id": r[0], "display_name": r[1]} for r in rows]

    def upsert(self, line_user_id: str, display_name: str,
               group_id: str | None = None,
               permission_level: str = Permission.STAFF) -> None:
        with self._db.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (line_user_id, display_name, permission_level, group_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (line_user_id)
                DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    group_id     = COALESCE(EXCLUDED.group_id, users.group_id),
                    updated_at   = NOW()
            """, (line_user_id, display_name, permission_level, group_id))

    def set_internal(self, line_user_id: str, display_name: str) -> None:
        with self._db.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (line_user_id, display_name, permission_level)
                VALUES (%s, %s, %s)
                ON CONFLICT (line_user_id)
                DO UPDATE SET
                    display_name     = EXCLUDED.display_name,
                    permission_level = %s,
                    updated_at       = NOW()
            """, (line_user_id, display_name, Permission.INTERNAL, Permission.INTERNAL))
