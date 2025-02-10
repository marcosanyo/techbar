#!/bin/bash

# フロントエンドの依存関係インストール
cd /workspace/frontend
if [ ! -f "package.json" ]; then
    # Next.js + TypeScript + TailwindCSSプロジェクトの作成
    npx create-next-app@latest . \
        --ts \
        --tailwind \
        --eslint \
        --app \
        --src-dir \
        --use-npm \
        --import-alias "@/*"
fi

# Terraformの初期化（必要な場合）
if [ -d "/workspace/terraform" ]; then
    cd /workspace/terraform
    terraform init
fi