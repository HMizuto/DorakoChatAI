import logging

from repositories.user_repository import UserRepository, Permission
from ai.qa_updater import QAUpdater
from line.messenger import LineMessenger


class DirectMessageHandler:
    def __init__(
        self,
        user_repo:  UserRepository,
        qa_updater: QAUpdater,
        messenger:  LineMessenger,
        logger:     logging.Logger,
    ):
        self._user_repo  = user_repo
        self._qa_updater = qa_updater
        self._messenger  = messenger
        self._logger     = logger

    async def handle(self, event, user_id: str, display_name: str, user_text: str) -> None:
        answer = self._route(user_id, display_name, user_text.strip())
        self._messenger.reply_text(event.reply_token, answer)
        self._logger.info(f"[1on1] replying to user_id={user_id}")

    def _route(self, user_id: str, display_name: str, command: str) -> str:
        if command == "社内メンバー登録":
            return self._cmd_register_internal(user_id, display_name)
        if command == "QA更新":
            return self._cmd_qa_update(user_id)
        return "コマンドが見つかりません。\n利用可能なコマンドは担当者にご確認ください。"

    def _cmd_register_internal(self, user_id: str, display_name: str) -> str:
        self._user_repo.set_internal(user_id, display_name)
        return f"社内メンバーとして登録しました。\n名前: {display_name}"

    def _cmd_qa_update(self, user_id: str) -> str:
        user = self._user_repo.get(user_id)
        if not user or user["permission_level"] != Permission.SYSADMIN:
            return "この機能はシステム管理者のみ使用できます。"

        result = self._qa_updater.run()

        if not result["success"]:
            return f"❌ QA更新に失敗しました。\n原因: {result['error']}"

        lines = ["✅ QA更新完了"]
        if result["inserted"] > 0:
            ids_str = ", ".join(f"No.{i}" for i in result["inserted_ids"])
            lines.append(f"・新規追加: {result['inserted']}件 ({ids_str})")
        if result["updated"] > 0:
            ids_str = ", ".join(f"No.{i}" for i in result["updated_ids"])
            lines.append(f"・更新: {result['updated']}件 ({ids_str})")
        if result["skipped"] > 0:
            lines.append(f"・スキップ: {result['skipped']}件")

        total = result["inserted"] + result["updated"] + result["skipped"]
        lines.append(f"合計: {total}件処理しました")
        return "\n".join(lines)
