# /workspace/Dockerfile

# フロントエンドのビルドステージ
FROM node:18 as frontend-builder

WORKDIR /workspace

# フロントエンドのソースコードをコピー
COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# バックエンドのビルドステージ
FROM python:3.11-slim

# システムパッケージのインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリの設定
WORKDIR /workspace

# バックエンドの依存関係をコピーしてインストール
COPY backend/src/functions/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# バックエンドのソースコードをコピー
COPY backend/src/functions/ .

# フロントエンドのビルド成果物をコピー
COPY --from=frontend-builder /workspace/dist frontend/dist

# Cloud Run用のポート設定
ENV PORT 8080

# Fastapiアプリケーションの起動
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
