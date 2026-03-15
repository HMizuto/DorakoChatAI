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
-- reason:  'RAG_MISS' | 'CONSULTATION' | 'REPORT'
-- status:  'OPEN' | 'RESOLVED'
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS escalations (
    id              SERIAL PRIMARY KEY,
    line_user_id    TEXT,
    display_name    TEXT,
    message         TEXT,
    reason          TEXT,
    status          TEXT        NOT NULL DEFAULT 'OPEN',
    group_id        TEXT,
    resolved_at     TIMESTAMPTZ,
    resolved_by     TEXT,
    executive_reply TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_escalations_group_status
    ON escalations (group_id, status);

-- ----------------------------------------
-- 会話ログテーブル
-- role(1on1): 'user' | 'assistant'
-- role(group): 'staff' | 'executive'
-- group_id が NULL の行 = 1on1 AI 会話履歴
-- group_id が SET  の行 = グループ会話記録（継続判定用）
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS conversation_logs (
    id           SERIAL PRIMARY KEY,
    line_user_id TEXT,
    role         TEXT,
    message      TEXT,
    group_id     TEXT,
    display_name TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conv_logs_group
    ON conversation_logs (group_id, created_at DESC);

-- ----------------------------------------
-- グループ設定テーブル
-- bot_mode: 'ACTIVE' | 'SILENT'
-- ACTIVE = BOTが応答する（初期状態）
-- SILENT = 幹部対応中のためBOTはログ保存のみ
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS group_settings (
    group_id   TEXT PRIMARY KEY,
    bot_mode   TEXT        NOT NULL DEFAULT 'ACTIVE',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
