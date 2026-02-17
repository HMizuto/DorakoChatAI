# -*- coding: utf-8 -*-
"""
rag_search.py - 最新 OpenAI API 対応版
-------------------------------------
ユーザーの質問を embedding 化し、
RDS(PostgreSQL + pgvector) から類似 chunk を検索し、
gpt-4o-mini で回答生成するテストスクリプト
"""
import psycopg2
from pgvector.psycopg2 import register_vector
from openai import OpenAI
import config as config
from memory.conversation_store import ConversationService
from pathlib import Path
# ベースプロンプト読み込み


BASE_DIR = Path(__file__).resolve().parents[1]
prompt_path = BASE_DIR / "docs" / "prompts" / "base_system_prompt.txt"

with open(prompt_path, "r", encoding="utf-8") as f:
    BASE_PROMPT = f.read()

# ----------------------------------------
# DB 接続
# ----------------------------------------
PG_HOST = config.PG_HOST
PG_PORT = config.PG_PORT
PG_DB = config.PG_DB
PG_USER = config.PG_USER
PG_PASSWORD = config.PG_PASSWORD


def get_conn():
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD
    )
    register_vector(conn)
    return conn


# ----------------------------------------
# 質問の embedding
# ----------------------------------------
def get_embedding(text: str):
    try:
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        
        print("Embedding対象:", text)

        res = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return res.data[0].embedding

    except Exception as e:
        print("🔥 embeddingエラー:", e)
        raise

# ----------------------------------------
# 類似検索
# ----------------------------------------
def search_similar_chunks(question, top_k=1, threshold=0.25):
    embedding = get_embedding(question)
    # embedding_str = "[" + ",".join(map(str, embedding)) + "]"

    conn = get_conn()
    cur = conn.cursor()

    print("embedding次元:", len(embedding))

    cur.execute("""
        SELECT
            question,
            answer,
            embedding <=> %s::vector AS distance
        FROM qa_vectors
        ORDER BY distance
        LIMIT %s
    """, (embedding, top_k))

    rows = cur.fetchall()
    conn.close()

    print("==== 生検索結果 ====")
    for r in rows:
        print("distance:", r[2])
    
    results = [
            {"question": r[0], "answer": r[1], "distance": r[2]}
            for r in rows if r[2] <= threshold
    ]
    return results


# ----------------------------------------
# RAG 回答生成（最新 API）
# ----------------------------------------
def answer_question(user_id: str, question: str):
    # ① ユーザー発言を保存
    ConversationService.save_message(user_id, "user", question)

    # ② 会話履歴取得
    history = ConversationService.get_recent_messages(user_id, limit=8)

    # ③ RAG検索
    chunks = search_similar_chunks(question)

    # ④ RAGなし → 通常会話
    if not chunks:
        answer = chat_with_ai_with_history(user_id, question)
        ConversationService.save_message(user_id, "assistant", answer)
        return answer

    # ⑤ context作成
    context_text = "\n\n".join(
        [f"Q: {c['question']}\nA: {c['answer']}" for c in chunks]
    )

    client = OpenAI(api_key=config.OPENAI_API_KEY)

    messages = [
        {"role": "system", "content": [{"type": "input_text", "text": BASE_PROMPT}]},
        *history,
        {
            "role": "system",
            "content": [{"type": "input_text", "text": f"以下は知識ベースです。無関係なら無視してください。\n{context_text}"}]
        },
        {"role": "user", "content": [{"type": "input_text", "text": question}]}
    ]

    response = client.responses.create(
        model="gpt-4o-mini",
        input=messages,
        temperature=0.2
    )

    answer = response.output_text

    # ⑥ AI発言を保存
    ConversationService.save_message(user_id, "assistant", answer)

    return answer



# ----------------------------------------
# Non-RAG 通常チャット
# ----------------------------------------
def chat_with_ai_with_history(user_id: str, user_text: str):
    history = ConversationService.get_recent_messages(user_id)

    client = OpenAI(api_key=config.OPENAI_API_KEY)

    messages = [
        {
            "role": "system",
            "content": [{"type": "input_text", "text": BASE_PROMPT}]
        },
        *history,
        {
            "role": "user",
            "content": [{"type": "input_text", "text": user_text}]
        }
    ]

    response = client.responses.create(
        model="gpt-4o-mini",
        input=messages,
        temperature=0.7
    )

    answer = response.output_text
    return answer




# ----------------------------------------
# テスト用 main
# ----------------------------------------
if __name__ == "__main__":
    q = input("質問を入力してください: ")
    ans = answer_question(q)
    print("\n=== 回答 ===")
    print(ans)