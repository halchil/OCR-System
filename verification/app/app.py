from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import pytesseract
from PIL import Image
import cv2
import numpy as np
from werkzeug.utils import secure_filename
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

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

def preprocess_image(image_path):
    """画像の前処理を行う"""
    # OpenCVで画像を読み込み
    image = cv2.imread(image_path)
    
    # グレースケール変換
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # ノイズ除去
    denoised = cv2.medianBlur(gray, 3)
    
    # 二値化
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # 前処理済み画像を保存
    processed_path = image_path.replace('.', '_processed.')
    cv2.imwrite(processed_path, binary)
    
    return processed_path

@app.route('/health', methods=['GET'])
def health_check():
    """ヘルスチェックエンドポイント"""
    return jsonify({'status': 'healthy', 'service': 'OCR API'})

@app.route('/ocr', methods=['POST'])
def ocr_process():
    """OCR処理のメインエンドポイント"""
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
        
        # 言語設定の取得（デフォルトは日本語+英語）
        languages = request.form.get('languages', 'jpn+eng')
        
        # 前処理の実行
        processed_filepath = preprocess_image(filepath)
        
        # OCR処理の実行
        try:
            # 前処理済み画像でOCR実行
            text_processed = pytesseract.image_to_string(
                Image.open(processed_filepath), 
                lang=languages,
                config='--psm 6'
            )
            
            # 元画像でもOCR実行（比較用）
            text_original = pytesseract.image_to_string(
                Image.open(filepath), 
                lang=languages,
                config='--psm 6'
            )
            
        except Exception as ocr_error:
            return jsonify({'error': f'OCR processing failed: {str(ocr_error)}'}), 500
        
        # 結果の保存
        result_data = {
            'filename': filename,
            'timestamp': timestamp,
            'languages': languages,
            'text_original': text_original.strip(),
            'text_processed': text_processed.strip(),
            'confidence': pytesseract.image_to_data(Image.open(processed_filepath), lang=languages, output_type=pytesseract.Output.DICT)
        }
        
        result_filename = f"{timestamp}_result.json"
        result_filepath = os.path.join(RESULTS_FOLDER, result_filename)
        
        with open(result_filepath, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        # レスポンス
        response_data = {
            'success': True,
            'filename': filename,
            'text_original': text_original.strip(),
            'text_processed': text_processed.strip(),
            'result_file': result_filename
        }
        
        return jsonify(response_data)
        
    except Exception as e:
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
    app.run(host='0.0.0.0', port=5000, debug=True)
