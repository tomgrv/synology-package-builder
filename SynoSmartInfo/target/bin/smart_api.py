#!/usr/bin/env python3
# Synology SMART API 서버 (Flask)

from flask import Flask, jsonify, Response
import subprocess

app = Flask(__name__)

SMART_SCRIPT = "/var/packages/SynoSmartInfo/target/bin/syno_smart_info.sh"

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
        # SMART 정보 텍스트 그대로 반환
        return Response(result.stdout, mimetype='text/plain; charset=utf-8')
    except subprocess.CalledProcessError as e:
        return jsonify({"error": "SMART info retrieval failed", "details": e.output}), 500

if __name__ == '__main__':
    # 0.0.0.0:8080 에서 실행 (포트는 필요 시 조정)
    app.run(host='0.0.0.0', port=8080)
