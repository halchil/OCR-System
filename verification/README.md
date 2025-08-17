# Tesseract OCR 検証システム

このプロジェクトは、Tesseract OCRを使用した画像からテキストを抽出する検証システムです。

## 構成

- **Tesseract OCR**: 画像からテキストを抽出するOCRエンジン
- **Nginx**: Webサーバーとリバースプロキシ
- **Flask API**: OCR処理を行うPythonアプリケーション
- **Web UI**: 画像アップロードと結果表示用のインターフェース

## 機能

- 画像ファイルのアップロード（PNG, JPG, JPEG, GIF, BMP, TIFF対応）
- 多言語対応（日本語、英語、中国語簡体字）
- 画像の前処理（グレースケール変換、ノイズ除去、二値化）
- 元画像と前処理後画像の両方でOCR実行
- 結果のJSON形式での保存
- 処理済みファイル一覧の表示

## 起動方法

### 1. 環境の準備

DockerとDocker Composeがインストールされていることを確認してください。

### 2. サービスの起動

```bash
cd verification
docker compose up -d
```

### 3. アクセス

- **Web UI**: http://localhost:8080
- **API**: http://localhost:5000
- **Nginx**: http://localhost:8080

## API エンドポイント

### OCR処理
- **POST** `/api/ocr`
  - 画像ファイルをアップロードしてOCR処理を実行
  - パラメータ:
    - `file`: 画像ファイル
    - `languages`: 言語設定（例: `jpn+eng`）

### ファイル一覧
- **GET** `/api/files`
  - アップロードされたファイルの一覧を取得

### 結果取得
- **GET** `/api/results/<filename>`
  - 指定されたファイルのOCR結果を取得

### ヘルスチェック
- **GET** `/api/health`
  - APIの状態確認

## ディレクトリ構造

```
verification/
├── docker-compose.yaml    # Docker Compose設定
├── nginx.conf            # Nginx設定
├── Dockerfile.app        # Pythonアプリケーション用Dockerfile
├── requirements.txt      # Python依存関係
├── app/
│   └── app.py           # Flaskアプリケーション
├── web/
│   └── index.html       # Web UI
├── uploads/             # アップロードされた画像ファイル
└── results/             # OCR処理結果
```

## 使用例

### Web UI からの使用

1. ブラウザで http://localhost:8080 にアクセス
2. 「ファイルを選択」ボタンをクリックして画像をアップロード
3. 言語設定を選択
4. 「OCR処理を実行」ボタンをクリック
5. 結果を確認

### API からの使用

```bash
# 画像ファイルをアップロードしてOCR処理
curl -X POST -F "file=@image.jpg" -F "languages=jpn+eng" http://localhost:5000/ocr

# ファイル一覧を取得
curl http://localhost:5000/files

# ヘルスチェック
curl http://localhost:5000/health
```

## 言語設定

- `jpn`: 日本語のみ
- `eng`: 英語のみ
- `jpn+eng`: 日本語 + 英語
- `jpn+eng+chi_sim`: 日本語 + 英語 + 中国語簡体字

## トラブルシューティング

### サービスが起動しない場合

```bash
# ログを確認
docker-compose logs

# 特定のサービスのログを確認
docker-compose logs tesseract
docker-compose logs nginx
docker-compose logs ocr-app
```

### ポートが使用中の場合

`docker-compose.yaml`のポート設定を変更してください：

```yaml
nginx:
  ports:
    - "8081:80"  # 8080を8081に変更

ocr-app:
  ports:
    - "5001:5000"  # 5000を5001に変更
```

### メモリ不足の場合

Dockerのメモリ制限を増やしてください。

## 停止方法

```bash
# サービスの停止
docker-compose down

# ボリュームも削除する場合
docker-compose down -v
```

## 注意事項

- アップロード可能なファイルサイズは16MBまで
- 対応画像形式: PNG, JPG, JPEG, GIF, BMP, TIFF
- 初回起動時はDockerイメージのダウンロードに時間がかかる場合があります
