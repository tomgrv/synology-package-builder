#!/bin/bash
# /var/packages/Synosmartinfo/target/bin/generate_smart_result.sh

RESULT_DIR="/usr/syno/synoman/webman/3rdparty/Synosmartinfo/result"
RESULT_FILE="$RESULT_DIR/smart.result"
TMP_FILE="$RESULT_FILE.tmp"
SMART_SCRIPT="/var/packages/Synosmartinfo/target/bin/syno_smart_info.sh"

# Ensure result directory exists
mkdir -p "$RESULT_DIR"
chmod 755 "$RESULT_DIR"

# 파라미터가 있으면 해당 옵션으로 실행, 없으면 기본 실행
if [ -n "$1" ]; then
    OPTION="$1"
else
    OPTION=""
fi

# Run SMART info script and save output atomically
if [ -n "$OPTION" ]; then
    sudo "$SMART_SCRIPT" "$OPTION" > "$TMP_FILE" 2>&1
else
    sudo "$SMART_SCRIPT" > "$TMP_FILE" 2>&1
fi

if [ $? -eq 0 ]; then
    mv "$TMP_FILE" "$RESULT_FILE"
    chmod 644 "$RESULT_FILE"
    echo "SMART result updated successfully with option: $OPTION"
    
    # 결과를 stdout으로도 출력 (api.cgi에서 바로 사용하기 위해)
    cat "$RESULT_FILE"
else
    echo "ERROR: Failed to run syno_smart_info.sh with option: $OPTION" > "$RESULT_FILE"
    if [ -f "$TMP_FILE" ]; then
        cat "$TMP_FILE" >> "$RESULT_FILE"
        rm -f "$TMP_FILE"
    fi
    chmod 644 "$RESULT_FILE"
    
    # 오류도 stdout으로 출력
    cat "$RESULT_FILE"
    exit 1
fi
