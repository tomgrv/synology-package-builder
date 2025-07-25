#!/bin/bash
###### 디버그 로그 출력 및 환경 검사
{
    echo "[DEBUG] === Environment Check $(date '+%Y-%m-%d %H:%M:%S') ==="
    echo "[DEBUG] PKG_ROOT=${PKG_ROOT}"
    echo "[DEBUG] TARGET_DIR=${TARGET_DIR}"
    echo "[DEBUG] BIN_DIR=${BIN_DIR}"
    echo "[DEBUG] LOG_DIR=${LOG_DIR}"
    echo "[DEBUG] STORAGE_SH=${STORAGE_SH}"
    echo "[DEBUG] CHANGE_PANEL_SH=${CHANGE_PANEL_SH}"
    echo "[DEBUG] --- File Permissions ---"
    ls -la "${BIN_DIR}" 2>&1
    echo "[DEBUG] --- Script Existence ---"
    [ -f "${STORAGE_SH}" ] && echo "[OK] ${STORAGE_SH} exists" || echo "[ERROR] ${STORAGE_SH} missing"
    [ -f "${CHANGE_PANEL_SH}" ] && echo "[OK] ${CHANGE_PANEL_SH} exists" || echo "[ERROR] ${CHANGE_PANEL_SH} missing"
    echo "[DEBUG] --- Script Permissions ---"
    [ -x "${STORAGE_SH}" ] && echo "[OK] ${STORAGE_SH} is executable" || echo "[ERROR] ${STORAGE_SH} not executable"
    [ -x "${CHANGE_PANEL_SH}" ] && echo "[OK] ${CHANGE_PANEL_SH} is executable" || echo "[ERROR] ${CHANGE_PANEL_SH} not executable"
    echo "[DEBUG] === Environment Check End ==="
} >> "${LOG_FILE}"

# ---------- 2. 로그 디렉터리 준비 -------------------------------------------####################################################################
# Storage Panel Manager – CGI API                                            #
# 위치 : @appstore/<패키지명>/ui/api.cgi                                     #
###############################################################################

# ---------- 1. 공통 변수 및 경로 계산 ---------------------------------------
# Synology 환경에서의 패키지 경로 계산
PKG_NAME="Changepanelsize"
PKG_ROOT="/var/packages/${PKG_NAME}"
TARGET_DIR="${PKG_ROOT}/target"
LOG_DIR="${PKG_ROOT}/var"
LOG_FILE="${LOG_DIR}/api.log"
BIN_DIR="${TARGET_DIR}/bin"
STORAGE_SH="${BIN_DIR}/storagepanel.sh"
CHANGE_PANEL_SH="${BIN_DIR}/change_panel_size.sh"

# 디버그 로그
echo "[DEBUG] STORAGE_SH=${STORAGE_SH}" >> "${LOG_FILE}"
echo "[DEBUG] CHANGE_PANEL_SH=${CHANGE_PANEL_SH}" >> "${LOG_FILE}"
ls -la "${BIN_DIR}" >> "${LOG_FILE}" 2>&1

# ---------- 2. 디렉터리 및 권한 준비 -------------------------------------------
# 로그 디렉터리
mkdir -p "${LOG_DIR}"
touch "${LOG_FILE}"
chmod 644 "${LOG_FILE}"

# 실행 권한 확인 및 설정
chmod +x "${STORAGE_SH}" 2>/dev/null || echo "[ERROR] Failed to chmod ${STORAGE_SH}" >> "${LOG_FILE}"
chmod +x "${CHANGE_PANEL_SH}" 2>/dev/null || echo "[ERROR] Failed to chmod ${CHANGE_PANEL_SH}" >> "${LOG_FILE}"

log() {
    # $1 = 메시지
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${LOG_FILE}"
}

# ---------- 3. HTTP 헤더(단 1회) 출력 ---------------------------------------
echo "Content-Type: application/json"
echo "Access-Control-Allow-Origin: *"
echo "Access-Control-Allow-Methods: GET, POST"
echo "Access-Control-Allow-Headers: Content-Type"
echo ""    # 헤더와 바디 구분용 공백 라인

# ---------- 4. URL-encoded 파라미터 파싱 ------------------------------------
# 안전한 urldecode 함수
urldecode() { : "${*//+/ }"; echo -e "${_//%/\\x}"; }

declare -A PARAM              # 연관배열에 파라미터 저장

parse_kv() {
    local kv_pair key val
    IFS='&' read -ra kv_pair <<< "$1"
    for pair in "${kv_pair[@]}"; do
        IFS='=' read -r key val <<< "${pair}"
        key="$(urldecode "${key}")"
        val="$(urldecode "${val}")"
        PARAM["${key}"]="${val}"
    done
}

case "$REQUEST_METHOD" in
    POST)
        read -r -t 30 POST_DATA || POST_DATA=""
        parse_kv "${POST_DATA}"
        ;;
    GET)
        parse_kv "${QUERY_STRING}"
        ;;
    *)
        log "Unsupported METHOD: ${REQUEST_METHOD}"
        echo '{"success":false,"message":"Unsupported METHOD"}'
        exit 0
        ;;
esac

ACTION="${PARAM[action]}"
HDD_BAY="${PARAM[hdd_bay]}"
SSD_BAY="${PARAM[ssd_bay]}"

log "Request: ACTION=${ACTION}, HDD_BAY=${HDD_BAY}, SSD_BAY=${SSD_BAY}"

# ---------- 5. JSON 응답 함수 -----------------------------------------------
json_response() {
    local success="$1" message="$2" data="$3"
    {
        echo "{"
        echo "  \"success\": ${success},"
        echo "  \"message\": \"${message//\"/\\\"}\""
        if [ -n "${data}" ]; then
            echo "  ,${data}"
        fi
        echo "}"
    }
}

# ---------- 6. 액션 라우팅 ---------------------------------------------------
_UNIQUE="$(/bin/get_key_value /etc.defaults/synoinfo.conf unique 2>/dev/null)"
_BUILD="$(/bin/get_key_value /etc.defaults/VERSION buildnumber 2>/dev/null)"

case "${ACTION}" in
    info)
        DATA="\"unique\":\"${_UNIQUE}\",\"build\":\"${_BUILD}\""
        json_response true "System information retrieved" "${DATA}"
        ;;

    apply)
        if [ -z "${HDD_BAY}" ] || [ -z "${SSD_BAY}" ]; then
            json_response false \
                "Missing parameters: hdd_bay and ssd_bay"
            exit 0
        fi
        
        log "Executing apply with HDD_BAY=${HDD_BAY}, SSD_BAY=${SSD_BAY}"
        
        # change_panel_size.sh를 통해 실행 (백그라운드 실행 후 결과 확인)
        TEMP_LOG="${LOG_DIR}/apply_temp.log"
        log "[DEBUG] Executing: ${CHANGE_PANEL_SH} apply ${HDD_BAY} ${SSD_BAY}"
        "${CHANGE_PANEL_SH}" apply "${HDD_BAY}" "${SSD_BAY}" > "${TEMP_LOG}" 2>&1 &
        APPLY_PID=$!
        log "[DEBUG] Started process with PID: ${APPLY_PID}"
        
        # 최대 30초 대기
        WAIT_COUNT=0
        while [ ${WAIT_COUNT} -lt 30 ]; do
            if ! kill -0 ${APPLY_PID} 2>/dev/null; then
                # 프로세스가 종료됨
                wait ${APPLY_PID}
                EXIT_CODE=$?
                break
            fi
            sleep 1
            WAIT_COUNT=$((WAIT_COUNT + 1))
        done
        
        # 여전히 실행 중이면 강제 종료
        if kill -0 ${APPLY_PID} 2>/dev/null; then
            kill ${APPLY_PID} 2>/dev/null
            EXIT_CODE=124  # timeout exit code
        fi
        
        # 결과를 메인 로그에 추가
        cat "${TEMP_LOG}" >> "${LOG_FILE}" 2>/dev/null
        
        if [ ${EXIT_CODE} -eq 0 ]; then
            log "Apply command completed successfully"
            json_response true \
                "Configuration applied: ${HDD_BAY} ${SSD_BAY}"
        else
            log "Apply command failed with exit code: ${EXIT_CODE}"
            ERR="$(tail -n 1 "${TEMP_LOG}" 2>/dev/null || echo 'Unknown error')"
            if [ ${EXIT_CODE} -eq 124 ]; then
                json_response false "Apply failed: Operation timed out after 30 seconds"
            else
                json_response false "Apply failed: ${ERR}"
            fi
        fi
        
        # 임시 로그 파일 정리
        rm -f "${TEMP_LOG}"
        ;;

    restore)
        log "Executing restore operation"
        
        # change_panel_size.sh를 통해 실행 (백그라운드 실행 후 결과 확인)
        TEMP_LOG="${LOG_DIR}/restore_temp.log"
        log "[DEBUG] Executing: ${CHANGE_PANEL_SH} restore"
        "${CHANGE_PANEL_SH}" restore > "${TEMP_LOG}" 2>&1 &
        RESTORE_PID=$!
        log "[DEBUG] Started restore process with PID: ${RESTORE_PID}"
        
        # 최대 30초 대기
        WAIT_COUNT=0
        while [ ${WAIT_COUNT} -lt 30 ]; do
            if ! kill -0 ${RESTORE_PID} 2>/dev/null; then
                # 프로세스가 종료됨
                wait ${RESTORE_PID}
                EXIT_CODE=$?
                break
            fi
            sleep 1
            WAIT_COUNT=$((WAIT_COUNT + 1))
        done
        
        # 여전히 실행 중이면 강제 종료
        if kill -0 ${RESTORE_PID} 2>/dev/null; then
            kill ${RESTORE_PID} 2>/dev/null
            EXIT_CODE=124  # timeout exit code
        fi
        
        # 결과를 메인 로그에 추가
        cat "${TEMP_LOG}" >> "${LOG_FILE}" 2>/dev/null
        
        if [ ${EXIT_CODE} -eq 0 ]; then
            log "Restore command completed successfully"
            json_response true "Original configuration restored"
        else
            log "Restore command failed with exit code: ${EXIT_CODE}"
            ERR="$(tail -n 1 "${TEMP_LOG}" 2>/dev/null || echo 'Unknown error')"
            if [ ${EXIT_CODE} -eq 124 ]; then
                json_response false "Restore failed: Operation timed out after 30 seconds"
            else
                json_response false "Restore failed: ${ERR}"
            fi
        fi
        
        # 임시 로그 파일 정리
        rm -f "${TEMP_LOG}"
        ;;

    start_service)
        # change_panel_size.sh를 데몬 모드로 시작
        if [ -f "${CHANGE_PANEL_SH}" ]; then
            nohup "${CHANGE_PANEL_SH}" daemon >> "${LOG_FILE}" 2>&1 &
            json_response true "Service started successfully"
        else
            json_response false "Service script not found: ${CHANGE_PANEL_SH}"
        fi
        ;;

    stop_service)
        # 실행 중인 change_panel_size.sh 프로세스 종료
        PID_FILE="${PKG_ROOT}/var/change_panel_size.pid"
        if [ -f "${PID_FILE}" ]; then
            PID=$(cat "${PID_FILE}" 2>/dev/null)
            if [ -n "${PID}" ] && kill -0 "${PID}" 2>/dev/null; then
                kill "${PID}"
                rm -f "${PID_FILE}"
                json_response true "Service stopped successfully"
            else
                rm -f "${PID_FILE}"
                json_response true "Service was not running"
            fi
        else
            json_response true "Service was not running"
        fi
        ;;

    status)
        # 서비스 상태 확인
        PID_FILE="${PKG_ROOT}/var/change_panel_size.pid"
        if [ -f "${PID_FILE}" ]; then
            PID=$(cat "${PID_FILE}" 2>/dev/null)
            if [ -n "${PID}" ] && kill -0 "${PID}" 2>/dev/null; then
                json_response true "Service is running" "\"pid\":\"${PID}\""
            else
                rm -f "${PID_FILE}"
                json_response false "Service is not running"
            fi
        else
            json_response false "Service is not running"
        fi
        ;;

    *)
        json_response false "Invalid action: ${ACTION}"
        ;;
esac
