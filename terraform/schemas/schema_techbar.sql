-- schema.sql

-- まずビューを削除
DROP VIEW IF EXISTS tech_bar_session_stats CASCADE;
DROP VIEW IF EXISTS tech_bar_inactive_sessions CASCADE;

-- トリガーと関数を削除
DROP TRIGGER IF EXISTS trigger_update_session_embedding ON tech_bar_messages CASCADE;
DROP FUNCTION IF EXISTS update_tech_bar_session_embedding() CASCADE;

-- テーブルを削除
DROP TABLE IF EXISTS tech_bar_related_messages CASCADE;
DROP TABLE IF EXISTS tech_bar_messages CASCADE;
DROP TABLE IF EXISTS tech_bar_conversations CASCADE;
DROP TABLE IF EXISTS tech_bar_sessions CASCADE;

-- 拡張機能を確認（既に存在する場合はスキップ）
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- セッションテーブル
CREATE TABLE tech_bar_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_key VARCHAR(64) NOT NULL,
    display_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    embedding vector(768),
    metadata JSONB DEFAULT '{}'::jsonb,
    combined_content TEXT,
    UNIQUE (session_key, display_name)
);

-- 会話テーブル
CREATE TABLE tech_bar_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES tech_bar_sessions(id),
    title TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_archived BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- メッセージテーブル
CREATE TABLE tech_bar_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES tech_bar_conversations(id),
    content TEXT NOT NULL,
    type VARCHAR(10) NOT NULL CHECK (type IN ('user', 'system')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    sequence_num INTEGER NOT NULL,
    embedding vector(768),
    UNIQUE (conversation_id, sequence_num)
);

-- 関連メッセージテーブル
CREATE TABLE tech_bar_related_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_message_id UUID NOT NULL REFERENCES tech_bar_messages(id),
    related_message_id UUID NOT NULL REFERENCES tech_bar_messages(id),
    similarity_score FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_tech_bar_relation UNIQUE (source_message_id, related_message_id)
);

-- インデックスの作成
CREATE INDEX idx_tech_bar_messages_conversation_id 
ON tech_bar_messages(conversation_id);

CREATE INDEX idx_tech_bar_conversations_session_id 
ON tech_bar_conversations(session_id);

CREATE INDEX idx_tech_bar_sessions_session_key 
ON tech_bar_sessions(session_key);

CREATE INDEX idx_tech_bar_sessions_active 
ON tech_bar_sessions(is_active) 
WHERE is_active = true;

CREATE INDEX idx_tech_bar_sessions_embedding 
ON tech_bar_sessions 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

CREATE INDEX idx_tech_bar_messages_embedding 
ON tech_bar_messages 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- セッション検索用の複合インデックス
CREATE INDEX idx_tech_bar_sessions_composite 
ON tech_bar_sessions(session_key, display_name, is_active);