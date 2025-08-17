from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import pytesseract
from PIL import Image
import cv2
import numpy as np
from werkzeug.utils import secure_filename
import json
import re
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

def extract_vehicle_number(text):
    """車両番号（ナンバープレート）を抽出する"""
    # 車両番号のパターン（例：品川500 あ 1234）
    patterns = [
        # 品川500 あ 1234 の形式
        r'([あ-ん]{2,3}\s*\d{1,4}\s*[あ-ん]\s*\d{1,4})',
        # 品川500あ1234 の形式（スペースなし）
        r'([あ-ん]{2,3}\d{1,4}[あ-ん]\d{1,4})',
        # 数字のみのパターン（車台番号など）
        r'(\d{4}[A-Z]\d{6})',  # 例：1234A123456
        r'([A-Z]{2}\d{2}[A-Z]{2}\d{4})',  # 例：AB12CD1234
    ]
    
    vehicle_numbers = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        vehicle_numbers.extend(matches)
    
    return vehicle_numbers



@app.route('/health', methods=['GET'])
def health_check():
    """ヘルスチェックエンドポイント"""
    return jsonify({'status': 'healthy', 'service': 'OCR API'})

@app.route('/ocr', methods=['POST'])
def ocr_process():
    """OCR処理のメインエンドポイント"""
    print("OCR処理開始")
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
        
        # OCR処理の実行
        try:
            print(f"OCR処理実行中... 言語: {languages}")
            # 画像でOCR実行
            text_result = pytesseract.image_to_string(
                Image.open(filepath), 
                lang=languages,
                config='--psm 6'
            )
            print("OCR処理完了")
            
        except Exception as ocr_error:
            print(f"OCR処理エラー: {str(ocr_error)}")
            return jsonify({'error': f'OCR processing failed: {str(ocr_error)}'}), 500
        
        # 車両番号の抽出
        vehicle_numbers = extract_vehicle_number(text_result)
        
        # 結果の保存
        result_data = {
            'filename': filename,
            'timestamp': timestamp,
            'languages': languages,
            'text_result': text_result.strip(),
            'vehicle_numbers': vehicle_numbers,
            'confidence': pytesseract.image_to_data(Image.open(filepath), lang=languages, output_type=pytesseract.Output.DICT)
        }
        
        result_filename = f"{timestamp}_result.json"
        result_filepath = os.path.join(RESULTS_FOLDER, result_filename)
        
        with open(result_filepath, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        # レスポンス
        response_data = {
            'success': True,
            'filename': filename,
            'text_result': text_result.strip(),
            'vehicle_numbers': vehicle_numbers,
            'result_file': result_filename
        }
        
        print("OCR処理完了、レスポンス送信")
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
