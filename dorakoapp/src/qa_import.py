import src.config as config

import pandas as pd
from openai import OpenAI
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()  # .envファイルを読み込む

df = pd.read_csv(config.SPREADSHEETURL)
print(df.head())

client = OpenAI(api_key=config.OPENAI_API_KEY)

def create_embedding(text: str) -> list:
    res = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return res.data[0].embedding



conn = psycopg2.connect(        
        host=config.PG_HOST,
        port=config.PG_PORT,
        dbname=config.PG_DB,
        user=config.PG_USER,
        password=config.PG_PASSWORD
        )
cursor = conn.cursor()

def fetch_existing_qa():
    cursor.execute(
        "SELECT id, created_at FROM qa_vectors"
    )
    return {row[0]: row[1] for row in cursor.fetchall()}

def upsert_qa(df):
    existing = fetch_existing_qa()

    for _, row in df.iterrows():
        qa_id = int(row["qa_id"])
        category = row.get("category")
        question = row["question"]
        answer = row["answer"]
        updated_at = row["updated_at"]

        # Embedding対象テキスト
        embedding_text = f"Q: {question}\nA: {answer}"

        # 既存判定
        if qa_id in existing:
            # updated_at が同じならスキップ
            if str(existing[qa_id]) == str(updated_at):
                continue

            # UPDATE
            embedding = create_embedding(embedding_text)

            cursor.execute(
                """
                UPDATE qa_vectors
                SET
                    category = %s,
                    question = %s,
                    answer = %s,
                    embedding = %s,
                    created_at = %s
                WHERE id = %s
                """,
                (
                    category,
                    question,
                    answer,
                    embedding,
                    updated_at,
                    qa_id
                )
            )
        else:
            # INSERT
            embedding = create_embedding(embedding_text)

            cursor.execute(
                """
                INSERT INTO qa_vectors
                (id, category, question, answer, embedding, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    qa_id,
                    category,
                    question,
                    answer,
                    embedding,
                    updated_at
                )
            )

    conn.commit()

if __name__ == "__main__":
    upsert_qa(df)