# backend/src/functions/database.py
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import DictCursor
import os
import logging
from google import genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        db_host = os.getenv('DB_HOST', 'localhost')
        if db_host.startswith('/cloudsql/'):
            # Cloud SQL Unix socket
            self.conn_params = {
                'dbname': os.getenv('DB_NAME', 'vector_db'),
                'user': os.getenv('DB_USER', 'vector_user'),
                'password': os.getenv('DB_PASSWORD', 'pass'),
                'host': db_host,  # Unix socketのパス
            }
        else:
            # ローカル開発環境
            self.conn_params = {
                'dbname': os.getenv('DB_NAME', 'vector_db'),
                'user': os.getenv('DB_USER', 'vector_user'),
                'password': os.getenv('DB_PASSWORD', 'pass'),
                'host': db_host,
                'port': os.getenv('DB_PORT', '5432')
            }
        
        # Gemini APIクライアントの初期化
        try:
            self.genai_client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        except Exception as e:
            logger.error(f"Gemini APIの初期化に失敗: {e}")
            self.genai_client = None
    
    def get_connection(self):
        return psycopg2.connect(**self.conn_params)
    
    def get_or_create_session(self, session_key: str, display_name: str) -> Optional[str]:
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # 既存のセッションを探す
                    cur.execute("""
                        SELECT id FROM tech_bar_sessions
                        WHERE session_key = %s AND display_name = %s
                        AND is_active = true
                    """, (session_key, display_name))
                    
                    result = cur.fetchone()
                    
                    if result:
                        session_id = result[0]
                        # アクティブ時間を更新
                        cur.execute("""
                            UPDATE tech_bar_sessions
                            SET last_active_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (session_id,))
                    else:
                        # 新しいセッションを作成
                        cur.execute("""
                            INSERT INTO tech_bar_sessions (session_key, display_name)
                            VALUES (%s, %s)
                            RETURNING id
                        """, (session_key, display_name))
                        session_id = cur.fetchone()[0]
                    
                    conn.commit()
                    return str(session_id)
                    
        except Exception as e:
            logger.error(f"セッション作成エラー: {e}")
            return None
    
    def get_active_users(self, timeout_minutes: int = 15) -> List[Dict[str, Any]]:
        """アクティブなユーザーを取得"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute("""
                        SELECT DISTINCT ON (display_name)
                            display_name,
                            last_active_at,
                            session_key
                        FROM tech_bar_sessions
                        WHERE is_active = true
                        AND last_active_at > NOW() - INTERVAL '%s minutes'
                        ORDER BY display_name, last_active_at DESC
                    """, (timeout_minutes,))
                    
                    rows = cur.fetchall()
                    return [
                        {
                            "display_name": row["display_name"],
                            "last_active": row["last_active_at"].isoformat(),
                            "session_key": row["session_key"]
                        }
                        for row in rows
                    ]
                    
        except Exception as e:
            logger.error(f"アクティブユーザー取得エラー: {e}")
            return []
    
    def get_recent_messages(self, limit: int = 5) -> List[str]:
        """最近のメッセージを取得"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute("""
                        SELECT m.content, m.type, m.metadata->>'display_name' as display_name
                        FROM tech_bar_messages m
                        JOIN tech_bar_conversations c ON m.conversation_id = c.id
                        WHERE c.is_archived = false
                        ORDER BY m.created_at DESC
                        LIMIT %s
                    """, (limit,))
                    
                    messages = cur.fetchall()
                    return [
                        f"{msg['display_name']}さん: {msg['content']}" if msg['type'] == 'user'
                        else f"マスター: {msg['content']}"
                        for msg in reversed(messages)
                    ]
                    
        except Exception as e:
            logger.error(f"最近のメッセージ取得エラー: {e}")
            return []
    
    def find_similar_conversations(
        self,
        content: str,
        display_name: str,
        similarity_threshold: float = 0.8,
        max_results: int = 3
    ) -> str:
        try:
            if not self.genai_client:
                return ""

            # 入力テキストのエンベディングを生成
            response = self.genai_client.models.embed_content(
                model="text-embedding-004",
                contents=content
            )
            
            if not response or not response.embeddings:
                logger.error("No embedding generated")
                return ""
                
            query_embedding = response.embeddings[0].values

            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    # インデックスを使用した効率的な検索
                    # 直前のメッセージを除外するために created_at で時間的な制限を追加
                    cur.execute("""
                        WITH SimilarMessages AS (
                            SELECT 
                                m.content,
                                m.metadata->>'display_name' as display_name,
                                1 - (m.embedding <=> %s::vector) as similarity,
                                ROW_NUMBER() OVER (
                                    PARTITION BY m.metadata->>'display_name'
                                    ORDER BY 1 - (m.embedding <=> %s::vector) DESC
                                ) as rank
                            FROM tech_bar_messages m
                            WHERE m.embedding IS NOT NULL
                            AND 1 - (m.embedding <=> %s::vector) > %s
                            AND m.created_at < (NOW() - INTERVAL '5 seconds')  -- 直前のメッセージを除外
                        )
                        SELECT *
                        FROM SimilarMessages
                        WHERE rank <= %s
                        ORDER BY similarity DESC
                    """, (
                        query_embedding,
                        query_embedding,
                        query_embedding,
                        similarity_threshold,
                        max_results
                    ))

                    results = cur.fetchall()
                    
                    if not results:
                        return ""

                    context_parts = []
                    
                    # 結果を整形
                    same_user_messages = [r for r in results if r['display_name'] == display_name]
                    other_user_messages = [r for r in results if r['display_name'] != display_name]

                    if same_user_messages:
                        context_parts.append("\n以前の関連する会話:")
                        for msg in same_user_messages:
                            context_parts.append(
                                f"{msg['display_name']}さん: {msg['content']}"
                            )

                    if other_user_messages:
                        context_parts.append("\n他のお客様との関連する会話:")
                        for msg in other_user_messages:
                            context_parts.append(
                                f"{msg['display_name']}さん: {msg['content']}"
                            )

                    return "\n".join(context_parts)

        except Exception as e:
            logger.error(f"類似会話検索エラー: {e}")
            return ""
        
    def get_or_create_conversation(self, session_id: str) -> Optional[str]:
        """セッションIDに対応する会話を取得または作成"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # アクティブな会話を探す
                    cur.execute("""
                        SELECT id FROM tech_bar_conversations
                        WHERE session_id = %s AND is_archived = false
                        ORDER BY created_at DESC
                        LIMIT 1
                    """, (session_id,))
                    
                    result = cur.fetchone()
                    
                    if result:
                        conversation_id = result[0]
                        # 最終更新時間を更新
                        cur.execute("""
                            UPDATE tech_bar_conversations
                            SET updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                            RETURNING id
                        """, (conversation_id,))
                    else:
                        # 新しい会話を作成
                        cur.execute("""
                            INSERT INTO tech_bar_conversations 
                            (session_id, title) 
                            VALUES (%s, %s)
                            RETURNING id
                        """, (session_id, f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
                        
                    conversation_id = cur.fetchone()[0]
                    conn.commit()
                    return str(conversation_id)
                    
        except Exception as e:
            logger.error(f"会話の取得/作成エラー: {e}")
            return None
        
    def save_message(
        self,
        conversation_id: str,
        content: str,
        message_type: str,
        metadata: Dict[str, Any]
    ) -> Optional[str]:
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # シーケンス番号の取得
                    cur.execute("""
                        SELECT COALESCE(MAX(sequence_num), 0) + 1
                        FROM tech_bar_messages
                        WHERE conversation_id = %s
                    """, (conversation_id,))
                    sequence_num = cur.fetchone()[0]
                    
                    # エンベディングの生成
                    embedding = None
                    if self.genai_client and message_type == 'user':
                        try:
                            response = self.genai_client.models.embed_content(
                                model="text-embedding-004",
                                contents=content
                            )
                            embedding = response.embeddings[0].values
                        except Exception as e:
                            logger.error(f"エンベディング生成エラー: {e}")
                    
                    # メッセージの保存
                    cur.execute("""
                        INSERT INTO tech_bar_messages
                        (conversation_id, content, type, metadata, sequence_num, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        conversation_id,
                        content,
                        message_type,
                        psycopg2.extras.Json(metadata),
                        sequence_num,
                        embedding
                    ))
                    
                    message_id = cur.fetchone()[0]
                    conn.commit()
                    return str(message_id)
                    
        except Exception as e:
            logger.error(f"メッセージ保存エラー: {e}")
            return None