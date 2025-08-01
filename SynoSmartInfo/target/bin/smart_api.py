#!/usr/bin/env python3
# Synology SMART API 서버 (Flask)

import logging
import os

PKG_NAME = "Synosmartinfo"
LOG_PATH = f"/var/packages/{PKG_NAME}/var/{PKG_NAME}.log"

# 로그 파일 핸들러 설정
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)  # 혹시 폴더가 없을 수 있으니
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_PATH, encoding='utf-8', mode='a'),
        logging.StreamHandler()
    ]
)

logging.info("Synology SMART Flask API Server Started")

from flask import Flask, jsonify, Response
import subprocess

app = Flask(__name__)

SMART_SCRIPT = "/var/packages/Synosmartinfo/target/bin/syno_smart_info.sh"

@app.route('/api/smartinfo')
def smart_info():
    try:
        result = subprocess.run(
            ['sudo', SMART_SCRIPT],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=True
        )
        logging.info("SMART INFO REQUEST SUCCESS")
        return Response(result.stdout, mimetype='text/plain; charset=utf-8')
    except subprocess.CalledProcessError as e:
        msg = f"SMART info retrieval failed: {str(e)} -- output: {getattr(e, 'output', '')}"
        logging.error(msg)
        return jsonify({"error": "SMART info retrieval failed", "details": getattr(e, "output", str(e))}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
