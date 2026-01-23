# 実行中のコンテナ一覧
docker ps

# すべてのコンテナ一覧
docker ps -a

# コンテナのログ確認
docker logs fastapi-container

# コンテナの停止
docker stop fastapi-container

# コンテナの削除
docker rm fastapi-container

# イメージの一覧
docker images

# イメージの削除
docker rmi my-fastapi-app

# ビルドと起動
docker-compose up --build

# バックグラウンドで起動
docker-compose up -d

# 停止
docker-compose down