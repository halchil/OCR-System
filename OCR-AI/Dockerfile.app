FROM python:3.9-slim

WORKDIR /app

# システム依存関係のインストール（最小限に）
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルのコピー
COPY app/ .

# ディレクトリの作成
RUN mkdir -p /app/uploads /app/results

EXPOSE 5000

CMD ["python", "app.py"]
