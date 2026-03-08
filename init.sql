-- ========================================
-- DorakoChatAI 初期化スクリプト
-- docker-compose 初回起動時に自動実行される
-- ========================================

-- pgvector 拡張
CREATE EXTENSION IF NOT EXISTS vector;

-- ----------------------------------------
-- ユーザー管理テーブル
-- permission_level: 'システム管理者' | '社内' | 'スタッフ'
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS users (
    line_user_id     TEXT PRIMARY KEY,
    display_name     TEXT,
    permission_level TEXT NOT NULL DEFAULT 'スタッフ',
    group_id         TEXT,
    registered_by    TEXT,
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ----------------------------------------
-- QAベクトルテーブル（RAG用）
-- embedding: text-embedding-3-small = 1536次元
-- created_at にはスプレッドシートの updated_at を格納
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS qa_vectors (
    id         BIGINT PRIMARY KEY,
    category   TEXT,
    question   TEXT,
    answer     TEXT,
    embedding  vector(1536),
    created_at TEXT
);

-- ----------------------------------------
-- エスカレーションテーブル
-- reason: 'RAG_MISS' | 'CONSULTATION' | 'REPORT'
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS escalations (
    id           SERIAL PRIMARY KEY,
    line_user_id TEXT,
    display_name TEXT,
    message      TEXT,
    reason       TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ----------------------------------------
-- 会話ログテーブル（会話履歴管理用）
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS conversation_logs (
    id           SERIAL PRIMARY KEY,
    line_user_id TEXT,
    role         TEXT,
    message      TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
