#!/bin/bash
# API endpoint for Storage Panel Manager

# 로그 파일 경로 지정 (적절한 위치와 권한 설정 필요)
LOG_DIR="/var/packages/Changepanelsize/var"
LOG_FILE="${LOG_DIR}/api.log"

# 로그 디렉터리 및 파일이 없으면 생성
mkdir -p "${LOG_DIR}"
touch "${LOG_FILE}"
chmod 644 "${LOG_FILE}"

# 요청 시각 기록 함수
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${LOG_FILE}"
}

# HTTP 헤더 출력 (CGI 기본)
echo "Content-Type: application/json"
echo "Access-Control-Allow-Origin: *"
echo "Access-Control-Allow-Methods: GET, POST"
echo "Access-Control-Allow-Headers: Content-Type"
echo ""

# 예: QUERY_STRING 가져오기
QUERY_STRING=${QUERY_STRING:-}

# 로그 남기기: 요청 수신
log_info "API 요청 수신: QUERY_STRING=${QUERY_STRING}"

# 요청 파라미터 예시(여기서는 단순 echo)
# 실제 로직 수행 부분 (예: storagepanel.sh 호출 등)
# 성공 시 로그 기록

if ./storagepanel.sh "${QUERY_STRING}" >> "${LOG_FILE}" 2>&1; then
    log_info "API 처리 성공"
    echo '{"status": "success"}'
else
    log_info "API 처리 실패"
    echo '{"status": "error"}'
fi

# Function to return JSON response
json_response() {
    local success="$1"
    local message="$2"
    local data="$3"
    
    echo "{"
    echo "  \"success\": $success,"
    echo "  \"message\": \"$message\""
    if [ -n "$data" ]; then
        echo "  ,"
        echo "  $data"
    fi
    echo "}"
}

# Parse request
if [ "$REQUEST_METHOD" = "POST" ]; then
    read -t 30 POST_DATA
    eval $(echo "$POST_DATA" | tr '&' ';')
elif [ "$REQUEST_METHOD" = "GET" ]; then
    eval $(echo "$QUERY_STRING" | tr '&' ';')
fi

# Get system information
_UNIQUE="$(/bin/get_key_value /etc.defaults/synoinfo.conf unique 2>/dev/null)"
_BUILD="$(/bin/get_key_value /etc.defaults/VERSION buildnumber 2>/dev/null)"

case "$action" in
    "info")
        # Return system information
        json_response "true" "System information retrieved" "\"unique\": \"${_UNIQUE}\", \"build\": \"${_BUILD}\""
        ;;
        
    "apply")
        if [ -z "$hdd_bay" ] || [ -z "$ssd_bay" ]; then
            json_response "false" "Missing required parameters: hdd_bay and ssd_bay"
            exit 0
        fi
        
        # Execute storage panel script
        RESULT=$(/var/packages/StoragePanelManager/target/bin/storagepanel.sh "$hdd_bay" "$ssd_bay" 2>&1)
        EXIT_CODE=$?
        
        if [ $EXIT_CODE -eq 0 ]; then
            json_response "true" "Configuration applied successfully: $hdd_bay $ssd_bay"
        else
            json_response "false" "Failed to apply configuration: $RESULT"
        fi
        ;;
        
    "restore")
        # Execute restore
        RESULT=$(/var/packages/StoragePanelManager/target/bin/storagepanel.sh -r 2>&1)
        EXIT_CODE=$?
        
        if [ $EXIT_CODE -eq 0 ]; then
            json_response "true" "Original configuration restored successfully"
        else
            json_response "false" "Failed to restore configuration: $RESULT"
        fi
        ;;
        
    *)
        json_response "false" "Invalid action specified"
        ;;
esac
