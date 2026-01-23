from fastapi import FastAPI, Request, BackgroundTasks
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from logging_config.log_config import setup_logger
from rag.rag_main import answer_question, chat_with_ai_with_history
from classifiers.message_classifier import ClassifierService
import config

# ロガー呼び出し
logger = setup_logger()
classifier = ClassifierService()
# ======================
#  FastAPI設定
# ======================
app = FastAPI()
line_bot_api = LineBotApi(config.CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(config.CHANNEL_SECRET)

# -----------------------------
# バックグラウンド処理
# -----------------------------
async def handle_events(events):
    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
            user_text = event.message.text
            user_id = event.source.user_id   # ★追加

            input_type = classifier.classify(user_text)

            # ★ 継続会話対応
            if input_type == "QUESTION":
                answer = answer_question(user_id, user_text)
            else:
                answer = chat_with_ai_with_history(user_id, user_text)

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=answer)
            )
            logger.info(f"replying: {event.reply_token}")


# ======================
#  Webhook API
# ======================
@app.post("/webhook")
async def webhook(request: Request, backgroundtask: BackgroundTasks):
    
    # body取得
    raw_body = await request.body()
    body = raw_body.decode("utf-8")

    # ★ログ：Webhook受信
    logger.info(f"Webhook received: {body}")

    # 署名とbody構造の確認
    signature = request.headers.get("X-Line-Signature")
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature")
        return "Invalid signature", 40
    except Exception as e:
        logger.error(f"Parse error: {str(e)}")
        return "Parse error", 400

    # 各イベントを処理(バックグラウンドタスク)
    backgroundtask.add_task(handle_events, events=events)

    # LINEサーバーへHTTP応答
    return "OK"