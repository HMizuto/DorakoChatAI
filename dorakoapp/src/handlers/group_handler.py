import logging

from repositories.user_repository import UserRepository
from repositories.escalation_repository import EscalationRepository
from repositories.conversation_repository import ConversationRepository
from ai.classifier import MessageClassifier
from ai.rag_service import RAGService
from ai.chat_service import ChatService
from ai.continuity_checker import ConversationContinuityChecker
from line.messenger import LineMessenger


class GroupEventHandler:
    def __init__(
        self,
        user_repo:           UserRepository,
        esc_repo:            EscalationRepository,
        conv_repo:           ConversationRepository,
        classifier:          MessageClassifier,
        rag_service:         RAGService,
        chat_service:        ChatService,
        continuity_checker:  ConversationContinuityChecker,
        messenger:           LineMessenger,
        logger:              logging.Logger,
    ):
        self._user_repo          = user_repo
        self._esc_repo           = esc_repo
        self._conv_repo          = conv_repo
        self._classifier         = classifier
        self._rag_service        = rag_service
        self._chat_service       = chat_service
        self._continuity_checker = continuity_checker
        self._messenger          = messenger
        self._logger             = logger

    async def handle(self, event, user_id: str, group_id: str,
                     display_name: str, user_text: str) -> None:

        self._user_repo.upsert(user_id, display_name, group_id=group_id)

        # ── 社内メンバー（幹部・管理者）の発言 ──────────────────────────
        if self._user_repo.is_internal(user_id):

            # @dorako → ACTIVE モード復帰
            if ConversationContinuityChecker.is_wake_up_call(user_text):
                self._continuity_checker.set_active(group_id)
                open_esc = self._esc_repo.get_open_in_group(group_id)
                if open_esc:
                    self._esc_repo.resolve(open_esc["id"], user_id, user_text)
                self._logger.info(
                    f"[Group] Bot resumed (ACTIVE) by {user_id} in group_id={group_id}"
                )
                return

            # 通常の幹部発言 → SILENT モードへ遷移 + ログ保存
            self._continuity_checker.set_silent(group_id)
            self._conv_repo.save_group_message(
                group_id, user_id, display_name, "executive", user_text
            )
            open_esc = self._esc_repo.get_open_in_group(group_id)
            if open_esc:
                self._esc_repo.resolve(open_esc["id"], user_id, user_text)
                self._logger.info(
                    f"[Escalation] resolved id={open_esc['id']} by {user_id}"
                )
            return  # BOT は返答しない

        # ── スタッフの発言 ────────────────────────────────────────────
        # 常にグループ会話ログに記録
        self._conv_repo.save_group_message(
            group_id, user_id, display_name, "staff", user_text
        )

        # SILENT モード → ログ保存のみ、応答しない
        if self._continuity_checker.is_ongoing(group_id):
            self._logger.info(
                f"[Group] SILENT mode, logging only: group_id={group_id}"
            )
            return

        # ACTIVE モード → 通常の分類・応答フロー
        input_type = self._classifier.classify(user_text)
        self._logger.info(f"[Group] input_type={input_type} / user_id={user_id}")

        executives = (
            self._user_repo.get_executives_in_group(group_id)
            if input_type in ("QUESTION", "CONSULTATION")
            else []
        )

        if input_type == "QUESTION":
            answer, rag_hit = self._rag_service.answer(user_id, user_text)
            if not rag_hit:
                self._esc_repo.save(user_id, display_name, user_text, "RAG_MISS", group_id)
                body = "申し訳ありません、この件はお答えできる情報が見つかりませんでした。ご確認をお願いいたします。"
                if executives:
                    self._messenger.reply_with_mention(event.reply_token, executives, body)
                else:
                    self._messenger.reply_text(event.reply_token, body)
                return

        elif input_type == "CONSULTATION":
            self._esc_repo.save(user_id, display_name, user_text, "CONSULTATION", group_id)
            answer = self._chat_service.chat(user_id, user_text)
            if executives:
                self._messenger.reply_with_mention(event.reply_token, executives, answer)
                return

        elif input_type == "REPORT":
            self._esc_repo.save(user_id, display_name, user_text, "REPORT", group_id)
            answer = self._chat_service.chat(user_id, user_text)

        else:  # CHAT / OTHER
            answer = self._chat_service.chat(user_id, user_text)

        self._messenger.reply_text(event.reply_token, answer)
        self._logger.info(f"[Group] replied: reply_token={event.reply_token}")
