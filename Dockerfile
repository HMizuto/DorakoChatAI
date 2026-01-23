FROM python:3.11-slim

WORKDIR /code

# PostgreSQL開発ライブラリをインストール
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# requirements.txtをコピー
COPY ./requirements.txt /code/requirements.txt

# pipをアップグレード
RUN pip install --upgrade pip

# 依存関係のインストール
RUN pip install --no-cache-dir -r /code/requirements.txt

# アプリケーションコードのコピー
COPY ./dorakoapp /code/dorakoapp

ENV PYTHONPATH=/code/dorakoapp/src

# ポートの公開
EXPOSE 8000

# アプリケーションの起動コマンド
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]