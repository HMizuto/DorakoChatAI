import unicodedata

from repositories.group_settings_repository import GroupSettingsRepository


class ConversationContinuityChecker:
    def __init__(self, group_settings_repo: GroupSettingsRepository):
        self._repo = group_settings_repo

    def is_ongoing(self, group_id: str) -> bool:
        """True → SILENT（BOTは返答しない）"""
        return self._repo.get_mode(group_id) == GroupSettingsRepository.SILENT

    def set_silent(self, group_id: str) -> None:
        """幹部が発言したとき → SILENTモードへ遷移"""
        self._repo.set_mode(group_id, GroupSettingsRepository.SILENT)

    def set_active(self, group_id: str) -> None:
        """@dorako で復帰したとき → ACTIVEモードへ遷移"""
        self._repo.set_mode(group_id, GroupSettingsRepository.ACTIVE)

    @staticmethod
    def is_wake_up_call(text: str) -> bool:
        """
        @dorako / @DORAKO / @Ｄｏｒａｋｏ（全角）/ @ドラ子 など
        表記ゆれをすべて吸収して復帰コールを検出する。
        """
        normalized = unicodedata.normalize("NFKC", text).lower()
        return "@dorako" in normalized or "@ドラ子" in normalized
