#!/bin/bash
# /var/services/web/Synosmartinfo/cgi-bin/smart_result.cgi

OUTPUT_FILE="/var/services/web/Synosmartinfo/result/smart.result"

echo "Content-Type: text/plain; charset=utf-8"
echo ""

if [[ -f "$OUTPUT_FILE" ]]; then
    cat "$OUTPUT_FILE"
else
    echo "SMART 정보 파일이 존재하지 않습니다."
fi
