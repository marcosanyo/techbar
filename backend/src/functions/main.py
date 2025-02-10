# backend/src/functions/main.py
from fastapi import FastAPI, WebSocket, HTTPException, Request  
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
from google import genai
import os
from dotenv import load_dotenv
import logging
import json
from database import Database
from pathlib import Path

# ロギングの設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# 環境変数のロード
load_dotenv()

# FastAPIアプリケーションの作成
app = FastAPI()

# フロントエンドのビルドディレクトリのパス
BASE_DIR = Path("/workspace")  # Dockerコンテナ内の作業ディレクトリ
FRONTEND_DIR = BASE_DIR / "frontend" / "dist"
logger.info(f"FRONTEND_DIR: {FRONTEND_DIR}")

# 静的ファイルのマウント（本番ビルド環境用）
if FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")

# Pydanticモデル
class Message(BaseModel):
    content: str = Field(..., description="メッセージの内容", min_length=1)
    type: str = Field(..., description="メッセージの種類", pattern="^(user|system)$")
    session_key: str = Field(..., description="セッションキー")
    display_name: str = Field(..., description="表示名")
    message_id: Optional[str] = Field(None, description="メッセージID")

    class Config:
        schema_extra = {
            "example": {
                "content": "こんばんは",
                "type": "user",
                "session_key": "abc123",
                "display_name": "ゲスト1",
                "message_id": "msg_1"
            }
        }

class UserEnterRequest(BaseModel):
    session_key: str
    display_name: str

    class Config:
        schema_extra = {
            "example": {
                "session_key": "abc123",
                "display_name": "ゲスト1"
            }
        }

# 静的ファイルの提供（本番ビルド環境用）
if FRONTEND_DIR.exists():
    @app.get("/favicon.ico")
    async def favicon():
        return FileResponse(str(FRONTEND_DIR / "favicon.ico"))

    @app.get("/")
    async def read_root():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限すること
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PostgreSQLデータベースのインスタンス
pg_db = Database()

# Gemini APIクライアントの初期化
try:
    genai_client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    logger.info("Gemini API client initialized successfully")
except Exception as e:
    logger.error(f"Gemini APIの初期化に失敗: {e}")
    genai_client = None

# WebSocket接続を管理する辞書
connected_users: Dict[str, WebSocket] = {}

def format_timestamp(dt: datetime) -> str:
    """タイムスタンプをISO 8601形式でZ付きに統一"""
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

# ユーティリティ関数
def construct_prompt(current_message: str, display_name: str, context: dict) -> str:
    prompt = f"""
    あなたは'深夜のテックバー'のベテランバーテンダー（マスター）として振る舞ってください。
    技術者たちが仕事帰りに立ち寄る、アットホームな雰囲気のバーです。
    お酒ではなく、技術の話題を提供するバーテンダーです。

    現在の状況:
    - 店内のお客様: {', '.join(f'{user}さん' for user in context['current_users'])}
    - 店内の雰囲気: {'quiet' if len(context['current_users']) <= 2 else 'lively'}
    - 発言したお客様: {display_name}さん

    以下の方針で接客してください:
    1. フレンドリーな口調で、でも礼儀正しく
    2. 他のお客様がいる場合は、全体の会話の流れを意識
    3. 技術の話題については詳しく、でも堅苦しくならないように
    4. 簡潔に返答
    5. 過去の会話に関連する内容があれば、自然な形で会話に織り交ぜる

    {context.get('similar_context', '')}
    
    そのまま返信になるので、括弧「」は不要です。
    盛り上がっていたり、口を出すべきでないと判断したら '...' のみを返答してください。

    直近の会話:
    {chr(10).join(context['recent_messages'])}
    """

    logger.debug(f"Generated prompt: {prompt}")
    return prompt

async def handle_websocket_message(message_data: dict):
    if message_data.get("type") == "welcome":
        # 入店時の歓迎メッセージを送信
        session_key = message_data.get("session_key")
        display_name = message_data.get("display_name")
        
        # システムメッセージ（入店通知）
        current_time = datetime.utcnow()
        formatted_time = format_timestamp(current_time)
        
        # system_message = {
        #     'type': 'message',
        #     'content': f"{display_name}さんが入店しました。",
        #     'display_name': 'system',
        #     'message_id': f"system_{uuid.uuid4()}",
        #     'timestamp': formatted_time,
        #     'system': True
        # }
        # await broadcast_message(json.dumps(system_message))

        # 2秒待機してからマスターの歓迎メッセージを送信
        await asyncio.sleep(1)
        
        active_users = pg_db.get_active_users()
        other_users = [u for u in active_users if u["display_name"] != display_name]
        
        welcome_message = f"いらっしゃいませ、{display_name}さん。"
        if other_users:
            welcome_message += f"\n今夜は{len(other_users)}名のお客様がいらっしゃいます。"
        welcome_message += "\nごゆっくりおくつろぎください。"

        master_time = datetime.utcnow()
        formatted_master_time = format_timestamp(master_time)
        
        master_message = {
            'type': 'message',
            'content': welcome_message,
            'display_name': 'マスター',
            'message_id': f"master_{uuid.uuid4()}",
            'timestamp': formatted_master_time,
            'system': False
        }
        await broadcast_message(json.dumps(master_message))

# WebSocketエンドポイント
@app.websocket("/ws/{session_key}")
async def websocket_endpoint(websocket: WebSocket, session_key: str):
    await websocket.accept()
    logger.info(f"WebSocket connection accepted for session: {session_key}")
    connected_users[session_key] = websocket
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received WebSocket message: {data}")
            try:
                message = json.loads(data)
                await handle_websocket_message(message)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                continue
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info(f"WebSocket connection closed for session: {session_key}")
        del connected_users[session_key]

async def broadcast_message(message: str):
    try:
        # メッセージが文字列でない場合はJSONに変換
        if not isinstance(message, str):
            message = json.dumps(message)
        
        logger.debug(f"Broadcasting message: {message}")
        # 全ての接続ユーザーにメッセージをブロードキャスト
        for session_key, websocket in connected_users.items():
            try:
                await websocket.send_text(message)
                logger.debug(f"Message sent to session: {session_key}")
            except Exception as e:
                logger.error(f"Error sending message to session {session_key}: {e}")
                continue
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")

# RESTエンドポイント
@app.post("/api/chat/message")
async def send_message(message: Message):
    try:
        logger.debug(f"Received message: {message.dict()}")
        
        if not message.session_key or not message.display_name:
            logger.error("Missing required fields")
            raise HTTPException(
                status_code=422,
                detail="session_key and display_name are required"
            )

        # セッション情報の取得または作成
        session_id = pg_db.get_or_create_session(
            session_key=message.session_key,
            display_name=message.display_name
        )
        
        if not session_id:
            logger.error(f"Failed to get session for {message.session_key}")
            raise HTTPException(status_code=404, detail="Session not found")
        
        conversation_id = pg_db.get_or_create_conversation(session_id)
        if not conversation_id:
            raise HTTPException(status_code=500, detail="Failed to create conversation")
        
        # ユーザーメッセージのタイムスタンプ
        user_timestamp = datetime.utcnow()
        formatted_user_timestamp = format_timestamp(user_timestamp)
        
        user_msg_id = pg_db.save_message(
            conversation_id=conversation_id,
            content=message.content,
            message_type='user',
            metadata={
                'timestamp': formatted_user_timestamp,
                'session_key': message.session_key,
                'display_name': message.display_name,
                'message_id': message.message_id
            }
        )

        # WebSocketを通じてユーザーメッセージをブロードキャスト
        await broadcast_message(json.dumps({
            'type': 'message',
            'content': message.content,
            'display_name': message.display_name,
            'message_id': message.message_id,
            'timestamp': formatted_user_timestamp,
            'system': False
        }))

        # Gemini APIを使用して応答を生成
        if message.type == 'user' and genai_client:
            context = {
                'current_users': [user['display_name'] for user in pg_db.get_active_users()],
                'recent_messages': pg_db.get_recent_messages(limit=5),
                'similar_context': pg_db.find_similar_conversations(
                    message.content,
                    message.display_name
                )
            }
            
            prompt = construct_prompt(message.content, message.display_name, context)
            
            try:
                response = await asyncio.to_thread(
                    genai_client.models.generate_content,
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                logger.info(f"Gemini API response: {response.text if response else 'No response'}")
            except Exception as e:
                logger.error(f"Error generating content with Gemini API: {e}")
                response = None
            
            if response and response.text:
                master_message_id = f"master_{uuid.uuid4()}"
                master_timestamp = datetime.utcnow() + timedelta(seconds=2)
                formatted_master_timestamp = format_timestamp(master_timestamp)
                
                master_msg_id = pg_db.save_message(
                    conversation_id=conversation_id,
                    content=response.text,
                    message_type='system',
                    metadata={
                        'timestamp': formatted_master_timestamp,
                        'session_key': 'master',
                        'display_name': 'マスター',
                        'message_id': master_message_id
                    }
                )
                
                await broadcast_message(json.dumps({
                    'type': 'message',
                    'content': response.text,
                    'display_name': 'マスター',
                    'message_id': master_message_id,
                    'timestamp': formatted_master_timestamp,
                    'system': False
                }))

        return {"status": "success", "message_id": user_msg_id}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Message processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/users/enter")
async def enter_bar(user: UserEnterRequest):
    try:
        logger.info(f"User entering bar: {user.dict()}")
        session_id = pg_db.get_or_create_session(
            session_key=user.session_key,
            display_name=user.display_name
        )
        
        if not session_id:
            raise HTTPException(
                status_code=500, 
                detail="Failed to create session"
            )
        
        active_users = pg_db.get_active_users()
        
        return {
            "status": "success",
            "session_id": session_id,
            "active_users": active_users
        }
        
    except Exception as e:
        logger.error(f"User enter error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/active")
async def get_active_users():
    try:
        users = pg_db.get_active_users()
        logger.debug(f"Active users: {users}")
        return {"users": users}
    except Exception as e:
        logger.error(f"Get active users error: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# アプリケーションの起動
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)