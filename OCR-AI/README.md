# ChatGPT OCR AI システム

このプロジェクトは、ChatGPT GPT-4 Vision APIを使用した高度な画像解析システムです。従来のTesseract OCRと比較して、より高精度で文脈を理解した画像解析が可能です。

## 🚀 主な特徴

- **ChatGPT GPT-4 Vision API**: 最新のAI技術を使用した画像解析
- **多言語対応**: 日本語、英語、その他多言語に対応
- **車両解析**: 車両番号、車種、色などの自動抽出
- **一般解析**: 文書、画像の種類、重要な情報の自動抽出
- **Web UI**: 直感的な操作インターフェース
- **Docker対応**: 簡単なセットアップとデプロイ

## 📋 システム構成

- **ChatGPT GPT-4 Vision API**: 画像解析エンジン
- **Nginx**: Webサーバーとリバースプロキシ
- **Flask API**: ChatGPT APIとの連携を行うPythonアプリケーション
- **Web UI**: 画像アップロードと結果表示用のインターフェース

## 🛠️ 機能

- 画像ファイルのアップロード（PNG, JPG, JPEG, GIF, BMP, TIFF対応）
- 2つの分析モード：
  - **一般解析**: 文書、画像の種類、重要な情報の抽出
  - **車両解析**: 車両番号、車種・メーカー、色の抽出
- 結果のJSON形式での保存
- 処理済みファイル一覧の表示
- ドラッグ&ドロップ対応

## 🚀 起動方法

### 1. 環境の準備

DockerとDocker Composeがインストールされていることを確認してください。

### 2. OpenAI API キーの設定

`.env`ファイルを作成してOpenAI APIキーを設定してください：

```bash
# OCR-AI/.env
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. サービスの起動

```bash
cd OCR-AI
docker compose up -d
```

### 4. アクセス

- **Web UI**: http://localhost:8081
- **API**: http://localhost:5001

## 📡 API エンドポイント

### OCR処理
- **POST** `/api/ocr`
  - 画像ファイルをアップロードしてChatGPT APIで解析
  - パラメータ:
    - `file`: 画像ファイル
    - `analysis_type`: 分析タイプ（`general` または `vehicle`）

### ファイル一覧
- **GET** `/api/files`
  - アップロードされたファイルの一覧を取得

### 結果取得
- **GET** `/api/results/<filename>`
  - 指定されたファイルの解析結果を取得

### ヘルスチェック
- **GET** `/api/health`
  - APIの状態確認

## 📁 ディレクトリ構造

```
OCR-AI/
├── docker-compose.yaml    # Docker Compose設定
├── nginx.conf            # Nginx設定
├── Dockerfile.app        # Pythonアプリケーション用Dockerfile
├── requirements.txt      # Python依存関係
├── .env                  # 環境変数（OpenAI APIキー）
├── app/
│   └── app.py           # Flaskアプリケーション
├── web/
│   └── index.html       # Web UI
├── uploads/             # アップロードされた画像ファイル
└── results/             # ChatGPT API解析結果
```

## 💡 使用例

### Web UI からの使用

1. ブラウザで http://localhost:8081 にアクセス
2. 「ファイルを選択」ボタンをクリックして画像をアップロード
3. 分析タイプを選択（一般解析 または 車両解析）
4. 「AI解析を実行」ボタンをクリック
5. ChatGPT APIによる解析結果を確認

### API からの使用

```bash
# 画像ファイルをアップロードして車両解析
curl -X POST -F "file=@car_image.jpg" -F "analysis_type=vehicle" http://localhost:5001/ocr

# 画像ファイルをアップロードして一般解析
curl -X POST -F "file=@document.jpg" -F "analysis_type=general" http://localhost:5001/ocr

# ファイル一覧を取得
curl http://localhost:5001/files

# ヘルスチェック
curl http://localhost:5001/health
```

## 🔧 分析タイプ

### 一般解析（general）
- 画像に含まれる全てのテキスト
- 重要な情報（日付、番号、名前など）
- 画像の種類・内容
- 詳細な分析結果

### 車両解析（vehicle）
- 車両番号（ナンバープレート）
- 車種・メーカー
- 色
- その他の重要な情報

## ⚠️ 注意事項

- **OpenAI APIキーが必要**: システムを使用するには有効なOpenAI APIキーが必要です
- **API使用料金**: ChatGPT APIの使用には料金が発生します
- **ファイルサイズ制限**: アップロード可能なファイルサイズは16MBまで
- **対応画像形式**: PNG, JPG, JPEG, GIF, BMP, TIFF
- **初回起動時**: Dockerイメージのダウンロードに時間がかかる場合があります

## 🛑 停止方法

```bash
# サービスの停止
docker-compose down

# ボリュームも削除する場合
docker-compose down -v
```

## 🔍 トラブルシューティング

### OpenAI API エラー

```bash
# ログを確認
docker-compose logs ocr-ai-app

# APIキーが正しく設定されているか確認
docker-compose exec ocr-ai-app env | grep OPENAI_API_KEY
```

### ポートが使用中の場合

`docker-compose.yaml`のポート設定を変更してください：

```yaml
nginx:
  ports:
    - "8082:80"  # 8081を8082に変更

ocr-ai-app:
  ports:
    - "5002:5000"  # 5001を5002に変更
```

### メモリ不足の場合

Dockerのメモリ制限を増やしてください。

## 📊 verificationシステムとの比較

| 機能 | verification (Tesseract) | OCR-AI (ChatGPT) |
|------|--------------------------|------------------|
| OCRエンジン | Tesseract 4 | ChatGPT GPT-4 Vision |
| 精度 | 標準 | 高精度 |
| 文脈理解 | 限定的 | 高度 |
| 多言語対応 | 言語パック必要 | 自動対応 |
| 車両解析 | 基本的なテキスト抽出 | 詳細な車両情報抽出 |
| API使用料金 | なし | あり |
| 処理速度 | 高速 | 中程度 |

## 🤝 貢献

このプロジェクトへの貢献を歓迎します。プルリクエストやイシューの報告をお気軽にお願いします。
