import logging

from repositories.user_repository import UserRepository
from repositories.escalation_repository import EscalationRepository
from ai.classifier import MessageClassifier
from ai.rag_service import RAGService
from ai.chat_service import ChatService
from line.messenger import LineMessenger


class GroupEventHandler:
    def __init__(
        self,
        user_repo:    UserRepository,
        esc_repo:     EscalationRepository,
        classifier:   MessageClassifier,
        rag_service:  RAGService,
        chat_service: ChatService,
        messenger:    LineMessenger,
        logger:       logging.Logger,
    ):
        self._user_repo    = user_repo
        self._esc_repo     = esc_repo
        self._classifier   = classifier
        self._rag_service  = rag_service
        self._chat_service = chat_service
        self._messenger    = messenger
        self._logger       = logger

    async def handle(self, event, user_id: str, group_id: str,
                     display_name: str, user_text: str) -> None:

        self._user_repo.upsert(user_id, display_name, group_id=group_id)

        if self._user_repo.is_internal(user_id):
            self._logger.info(f"[Group] Skipped internal member: user_id={user_id}")
            return

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
                self._esc_repo.save(user_id, display_name, user_text, "RAG_MISS")
                body = "申し訳ありません、この件はお答えできる情報が見つかりませんでした。ご確認をお願いいたします。"
                if executives:
                    self._messenger.reply_with_mention(event.reply_token, executives, body)
                else:
                    self._messenger.reply_text(event.reply_token, body)
                return

        elif input_type == "CONSULTATION":
            self._esc_repo.save(user_id, display_name, user_text, "CONSULTATION")
            answer = self._chat_service.chat(user_id, user_text)
            if executives:
                self._messenger.reply_with_mention(event.reply_token, executives, answer)
                return

        elif input_type == "REPORT":
            self._esc_repo.save(user_id, display_name, user_text, "REPORT")
            answer = self._chat_service.chat(user_id, user_text)

        else:  # CHAT / OTHER
            answer = self._chat_service.chat(user_id, user_text)

        self._messenger.reply_text(event.reply_token, answer)
        self._logger.info(f"[Group] replying: {event.reply_token}")
