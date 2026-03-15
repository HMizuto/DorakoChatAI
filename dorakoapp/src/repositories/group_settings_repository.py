from core.database import Database


class GroupSettingsRepository:
    ACTIVE = "ACTIVE"
    SILENT = "SILENT"

    def __init__(self, db: Database):
        self._db = db

    def get_mode(self, group_id: str) -> str:
        """グループのBOTモードを返す。レコードがなければ ACTIVE。"""
        with self._db.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT bot_mode FROM group_settings WHERE group_id = %s",
                (group_id,),
            )
            row = cur.fetchone()
        return row[0] if row else self.ACTIVE

    def set_mode(self, group_id: str, mode: str) -> None:
        """グループのBOTモードを更新する（UPSERT）。"""
        with self._db.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO group_settings (group_id, bot_mode)
                VALUES (%s, %s)
                ON CONFLICT (group_id)
                DO UPDATE SET bot_mode = EXCLUDED.bot_mode, updated_at = NOW()
            """, (group_id, mode))
