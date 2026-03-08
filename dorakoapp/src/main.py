from fastapi import FastAPI, Request, BackgroundTasks
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage

from logging_config.log_config import setup_logger
from core.config import settings
from core.database import Database
from repositories.user_repository import UserRepository
from repositories.escalation_repository import EscalationRepository
from repositories.conversation_repository import ConversationRepository
from repositories.qa_repository import QARepository
from ai.classifier import MessageClassifier
from ai.rag_service import RAGService
from ai.chat_service import ChatService
from ai.qa_updater import QAUpdater
from line.messenger import LineMessenger
from handlers.group_handler import GroupEventHandler
from handlers.direct_handler import DirectMessageHandler

# ======================
#  ロガー
# ======================
logger = setup_logger()

# ======================
#  DI 組み立て
# ======================
db           = Database(settings)
user_repo    = UserRepository(db)
esc_repo     = EscalationRepository(db)
conv_repo    = ConversationRepository(db)
qa_repo      = QARepository(db)
classifier   = MessageClassifier(settings)
rag_service  = RAGService(qa_repo, conv_repo, settings)
chat_service = ChatService(conv_repo, settings)
qa_updater   = QAUpdater(qa_repo, settings)
messenger    = LineMessenger(settings)

group_handler  = GroupEventHandler(user_repo, esc_repo, classifier, rag_service, chat_service, messenger, logger)
direct_handler = DirectMessageHandler(user_repo, qa_updater, messenger, logger)

# ======================
#  FastAPI / LINE SDK
# ======================
app          = FastAPI()
line_bot_api = LineBotApi(settings.line_channel_access_token)
parser       = WebhookParser(settings.line_channel_secret)


# ======================
#  バックグラウンド処理
# ======================
async def handle_events(events):
    for event in events:
        if not (isinstance(event, MessageEvent) and isinstance(event.message, TextMessage)):
            continue

        user_text = event.message.text
        user_id   = event.source.user_id

        if event.source.type == "group":
            group_id = event.source.group_id
            profile  = line_bot_api.get_group_member_profile(group_id, user_id)
            logger.info(f"[Group] group_id={group_id} / user_id={user_id}")
            await group_handler.handle(event, user_id, group_id, profile.display_name, user_text)
        else:
            profile = line_bot_api.get_profile(user_id)
            logger.info(f"[1on1] user_id={user_id}")
            await direct_handler.handle(event, user_id, profile.display_name, user_text)


# ======================
#  Webhook API
# ======================
@app.post("/webhook")
async def webhook(request: Request, backgroundtask: BackgroundTasks):
    raw_body = await request.body()
    body     = raw_body.decode("utf-8")
    logger.info(f"Webhook received: {body}")

    signature = request.headers.get("X-Line-Signature")
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature")
        return "Invalid signature", 400
    except Exception as e:
        logger.error(f"Parse error: {str(e)}")
        return "Parse error", 400

    backgroundtask.add_task(handle_events, events=events)
    return "OK"


# ヘルスチェック用
@app.get("/health")
def health():
    return {"status": "ok"}
