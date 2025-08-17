from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import base64
import json
import re
from datetime import datetime
from werkzeug.utils import secure_filename
import openai
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

app = Flask(__name__)
CORS(app)

# OpenAI API設定（0.28.1バージョン対応）
openai.api_key = os.getenv('OPENAI_API_KEY')

# デバッグ用のログ設定
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 設定
UPLOAD_FOLDER = '/app/uploads'
RESULTS_FOLDER = '/app/results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

# ディレクトリの作成
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def encode_image_to_base64(image_path):
    """画像をBase64エンコードする"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_image_with_gpt(image_path, analysis_type="general"):
    """ChatGPT APIを使用して画像を解析する"""
    try:
        # 画像をBase64エンコード
        base64_image = encode_image_to_base64(image_path)
        
        # 分析タイプに応じたプロンプトを設定
        if analysis_type == "vehicle":
            prompt = """
            この画像を分析して、車両番号（ナンバープレート）を抽出してください。
            
            重要：必ずJSON形式で回答してください。テキスト説明は不要です。
            
            以下の情報を抽出し、指定されたJSON形式で返してください：
            
            1. 車両番号（日本のナンバープレート形式：品川500 あ 1234、品川500あ1234、車台番号：1234A123456など）
            2. 車種・メーカー名
            3. 車両の色
            4. その他の重要な車両情報
            
            回答は必ず以下のJSON形式のみで返してください：
            {
                "vehicle_number": "検出された車両番号",
                "vehicle_type": "車種・メーカー名",
                "color": "車両の色",
                "other_info": "その他の重要な車両情報",
                "full_text": "画像から読み取れる全てのテキスト",
                "confidence": "車両番号の検出確信度（高/中/低）"
            }
            
            車両番号が見つからない場合は、vehicle_numberを空文字列にしてください。
            JSON以外の説明文は一切含めないでください。
            """
        else:
            prompt = """
            この画像を分析してください。
            
            重要：必ずJSON形式で回答してください。テキスト説明は不要です。
            
            以下の情報を抽出し、指定されたJSON形式で返してください：
            
            1. 画像に含まれる全てのテキスト
            2. 重要な情報（日付、番号、名前など）
            3. 画像の種類・内容
            
            回答は必ず以下のJSON形式のみで返してください：
            {
                "text_content": "画像から読み取れる全てのテキスト",
                "important_info": "重要な情報",
                "image_type": "画像の種類・内容",
                "analysis": "詳細な分析結果"
            }
            
            JSON以外の説明文は一切含めないでください。
            """
        
        # デバッグ情報の出力
        logger.debug(f"API呼び出し開始 - 分析タイプ: {analysis_type}")
        logger.debug(f"プロンプト: {prompt[:200]}...")
        logger.debug(f"画像サイズ: {len(base64_image)} bytes")
        
        # ChatGPT API呼び出し（0.28.1バージョン対応）
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            logger.debug(f"APIレスポンス受信: {response}")
            
            # レスポンスからJSONを抽出
            content = response.choices[0].message.content
            logger.debug(f"API応答内容: {content[:200]}...")
            
        except Exception as api_error:
            logger.error(f"API呼び出しエラー詳細: {str(api_error)}")
            logger.error(f"エラータイプ: {type(api_error)}")
            raise api_error
        
        # JSON部分を抽出（```json で囲まれている場合）
        logger.debug("JSON解析開始")
        logger.debug(f"API応答全体: {content}")
        
        # まず、```json で囲まれた部分を探す
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            logger.debug("JSONブロックを検出")
        else:
            # JSONブロックが見つからない場合、{}で囲まれた部分を探す
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                logger.debug("JSONオブジェクトを検出")
            else:
                # それでも見つからない場合は、内容全体をパース
                json_str = content
                logger.debug("JSONブロックが見つからないため、全体をパース")
        
        logger.debug(f"パース対象JSON文字列: {json_str[:200]}...")
        
        # JSONとしてパース
        try:
            result = json.loads(json_str)
            logger.debug(f"JSON解析成功: {result}")
        except json.JSONDecodeError as json_error:
            logger.error(f"JSON解析エラー: {str(json_error)}")
            logger.error(f"パース失敗した文字列: {json_str}")
            # JSONパースに失敗した場合は、テキストとして扱う
            result = {
                "text_content": content,
                "analysis": f"JSON形式での解析に失敗しました。エラー: {str(json_error)}。テキスト形式で結果を返します。"
            }
        
        logger.debug(f"最終結果: {result}")
        return result
        
    except Exception as e:
        logger.error(f"ChatGPT API エラー: {str(e)}")
        logger.error(f"エラーの詳細: {type(e).__name__}")
        return {"error": f"API呼び出しエラー: {str(e)}"}

def extract_vehicle_number(text):
    """車両番号（ナンバープレート）を抽出する"""
    patterns = [
        # 日本のナンバープレート形式（品川500 あ 1234）
        r'([あ-ん]{2,3}\s*\d{1,4}\s*[あ-ん]\s*\d{1,4})',
        # 日本のナンバープレート形式（スペースなし）
        r'([あ-ん]{2,3}\d{1,4}[あ-ん]\d{1,4})',
        # 車台番号形式（1234A123456）
        r'(\d{4}[A-Z]\d{6})',
        # 国際ナンバープレート形式（AB12CD1234）
        r'([A-Z]{2}\d{2}[A-Z]{2}\d{4})',
        # 数字のみの車両番号
        r'(\d{3,4}[-\s]?\d{3,4})',
        # 英数字混合の車両番号
        r'([A-Z0-9]{4,8})',
    ]
    
    vehicle_numbers = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        vehicle_numbers.extend(matches)
    
    # 重複を除去
    vehicle_numbers = list(set(vehicle_numbers))
    
    return vehicle_numbers

@app.route('/health', methods=['GET'])
def health_check():
    """ヘルスチェックエンドポイント"""
    # デバッグ情報を追加
    api_key = os.getenv('OPENAI_API_KEY')
    api_key_status = "設定済み" if api_key else "未設定"
    
    return jsonify({
        'status': 'healthy', 
        'service': 'OCR AI API',
        'debug_info': {
            'api_key_status': api_key_status,
            'api_key_length': len(api_key) if api_key else 0,
            'openai_api_configured': openai.api_key is not None,
            'upload_folder_exists': os.path.exists(UPLOAD_FOLDER),
            'results_folder_exists': os.path.exists(RESULTS_FOLDER)
        }
    })

@app.route('/test-api', methods=['GET'])
def test_api():
    """OpenAI API接続テストエンドポイント"""
    try:
        logger.info("OpenAI API接続テスト開始")
        
        # 簡単なテキスト生成テスト
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": "こんにちは"}
            ],
            max_tokens=10
        )
        
        logger.info("OpenAI API接続テスト成功")
        return jsonify({
            'status': 'success',
            'message': 'OpenAI API接続成功',
            'response': response.choices[0].message.content
        })
        
    except Exception as e:
        logger.error(f"OpenAI API接続テスト失敗: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'OpenAI API接続失敗: {str(e)}',
            'error_type': type(e).__name__
        }), 500

@app.route('/ocr', methods=['POST'])
def ocr_process():
    """OCR処理のメインエンドポイント"""
    logger.info("OCR AI処理開始")
    logger.debug(f"リクエストヘッダー: {dict(request.headers)}")
    logger.debug(f"リクエストファイル: {request.files}")
    logger.debug(f"リクエストメソッド: {request.method}")
    logger.debug(f"リクエストURL: {request.url}")
    
    try:
        # ファイルの確認
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # ファイル名の安全化
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        # ファイルの保存
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 分析タイプの取得（デフォルトはgeneral）
        analysis_type = request.form.get('analysis_type', 'general')
        
        # ChatGPT APIを使用した画像解析
        try:
            logger.info(f"ChatGPT API解析実行中... 分析タイプ: {analysis_type}")
            logger.debug(f"ファイルパス: {filepath}")
            analysis_result = analyze_image_with_gpt(filepath, analysis_type)
            logger.info("ChatGPT API解析完了")
            logger.debug(f"解析結果: {analysis_result}")
            
        except Exception as api_error:
            logger.error(f"API解析エラー: {str(api_error)}")
            logger.error(f"エラータイプ: {type(api_error)}")
            return jsonify({'error': f'API analysis failed: {str(api_error)}'}), 500
        
        # 車両番号の抽出（テキストから）
        text_content = ""
        if analysis_type == "vehicle":
            text_content = analysis_result.get('full_text', '')
        else:
            text_content = analysis_result.get('text_content', '')
        
        vehicle_numbers = extract_vehicle_number(text_content)
        
        # ChatGPT APIから取得した車両番号も追加
        api_vehicle_number = analysis_result.get('vehicle_number', '')
        if api_vehicle_number and api_vehicle_number not in vehicle_numbers:
            vehicle_numbers.append(api_vehicle_number)
        
        # 結果の保存
        result_data = {
            'filename': filename,
            'timestamp': timestamp,
            'analysis_type': analysis_type,
            'analysis_result': analysis_result,
            'vehicle_numbers': vehicle_numbers,
            'api_used': 'ChatGPT GPT-4 Vision',
            'processing_info': {
                'total_vehicle_numbers_found': len(vehicle_numbers),
                'api_vehicle_number': api_vehicle_number,
                'regex_vehicle_numbers': extract_vehicle_number(text_content),
                'confidence': analysis_result.get('confidence', 'unknown')
            }
        }
        
        result_filename = f"{timestamp}_result.json"
        result_filepath = os.path.join(RESULTS_FOLDER, result_filename)
        
        with open(result_filepath, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        # レスポンス
        response_data = {
            'success': True,
            'filename': filename,
            'analysis_result': analysis_result,
            'vehicle_numbers': vehicle_numbers,
            'result_file': result_filename,
            'api_used': 'ChatGPT GPT-4 Vision'
        }
        
        logger.info("OCR AI処理完了、レスポンス送信")
        logger.debug(f"レスポンスデータ: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"サーバーエラー: {str(e)}")
        logger.error(f"エラータイプ: {type(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/results/<filename>', methods=['GET'])
def get_result(filename):
    """結果ファイルの取得"""
    try:
        result_path = os.path.join(RESULTS_FOLDER, filename)
        if os.path.exists(result_path):
            return send_file(result_path, mimetype='application/json')
        else:
            return jsonify({'error': 'Result file not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Error reading result: {str(e)}'}), 500

@app.route('/files', methods=['GET'])
def list_files():
    """アップロードされたファイルの一覧取得"""
    try:
        files = []
        for filename in os.listdir(UPLOAD_FOLDER):
            if allowed_file(filename):
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                files.append({
                    'filename': filename,
                    'size': os.path.getsize(filepath),
                    'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                })
        
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': f'Error listing files: {str(e)}'}), 500

if __name__ == '__main__':
    logger.info("Flaskアプリケーション起動開始")
    logger.info(f"OpenAI APIキー設定状況: {'設定済み' if os.getenv('OPENAI_API_KEY') else '未設定'}")
    logger.info(f"アップロードフォルダ: {UPLOAD_FOLDER}")
    logger.info(f"結果フォルダ: {RESULTS_FOLDER}")
    app.run(host='0.0.0.0', port=5000, debug=True)
