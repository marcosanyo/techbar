# 深夜のテックバー 🌃

匿名の技術者が集まり、AI バーテンダーと気軽に会話できる仮想バー空間です。
PostgreSQL の Vector Search と Google Gemini API を組み合わせて、自然な会話の流れを実現しています。

## 機能

- 🤖 AI バーテンダーによる自然な会話進行
- 👥 WebSocket によるリアルタイムチャット
- 🎭 匿名性を重視したセッション管理
- 🔍 Vector Search による関連会話の自然な引用
- 🌙 シンプルな UI とダークテーマ

## 技術スタック

### フロントエンド
- Vue.js 3
- Vuetify 3
- vue-advanced-chat
- WebSocket

### バックエンド
- FastAPI
- PostgreSQL + pg_vector
- Google Cloud Gemini API

### インフラ
- Google Cloud Run
- Google Cloud SQL
- Terraform

## 開発環境のセットアップ

### 前提条件
- Python 3.11
- Node.js 18
- PostgreSQL 14+
- Terraform
- Google Cloud SDK
- Cloud SQL Proxy

### 環境変数の設定

`.env` ファイルを作成:
```bash
GEMINI_API_KEY=your-api-key
PROJECT_ID=your-project-id
REGION=asia-northeast1
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your-db-name
DB_USER=your-username
DB_PASSWORD=your-password
DB_INSTANCE_NAME=your-instance-name
FUNCTIONS_EMULATOR=true
```

### データベースのセットアップ

1. PostgreSQL の起動確認
```bash
PGPASSWORD=pass psql -h localhost -p 5432 -U vector_user -d vector_db
```

2. スキーマの適用
```bash
PGPASSWORD=pass psql -h localhost -p 5432 -U vector_user -d vector_db -f terraform/schemas/schema.sql
```

### アプリケーションの起動

1. フロントエンドの開発サーバー起動
```bash
cd frontend
npm install
npm run serve
```

2. バックエンドの開発サーバー起動
```bash
cd backend/src/functions
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8083
```

## デプロイ手順

### 1. GCP プロジェクトの設定
```bash
gcloud auth login --no-launch-browser
gcloud config set project information-exchange-agent
```

### 2. Terraform によるインフラのデプロイ
```bash
cd terraform/environments/dev
terraform init
terraform apply
```

### 3. アプリケーションのビルドとデプロイ
```bash
./deploy_gcloud_auto.sh
```

## ライセンス

MIT
