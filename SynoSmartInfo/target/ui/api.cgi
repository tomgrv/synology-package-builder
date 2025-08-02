#!/bin/bash

#########################################################################
# Synology SMART Info API - CGI API                                    #
# 위치: @appstore/SynoSmartInfo/ui/api.cgi                              #
#########################################################################

# --------- 1. 공통 변수 및 경로 계산 ---------------------------------
PKG_NAME="Synosmartinfo"
PKG_ROOT="/var/packages/${PKG_NAME}"
TARGET_DIR="${PKG_ROOT}/target"
LOG_DIR="${PKG_ROOT}/var"
LOG_FILE="${LOG_DIR}/api.log"
BIN_DIR="${TARGET_DIR}/bin"
SMART_INFO_SH="${BIN_DIR}/syno_smart_info.sh"
GENERATE_RESULT_SH="${BIN_DIR}/generate_smart_result.sh"

# --------- 2. 디렉터리 및 권한 준비 -----------------------------------
mkdir -p "${LOG_DIR}"
touch "${LOG_FILE}"
chmod 644 "${LOG_FILE}"

# 실행 권한 확인 및 설정
chmod +x "${SMART_INFO_SH}" 2>/dev/null || echo "[ERROR] Failed to chmod ${SMART_INFO_SH}" >> "${LOG_FILE}"
chmod +x "${GENERATE_RESULT_SH}" 2>/dev/null || echo "[ERROR] Failed to chmod ${GENERATE_RESULT_SH}" >> "${LOG_FILE}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${LOG_FILE}"
}

# --------- 3. HTTP 헤더 출력 ----------------------------------------
echo "Content-Type: application/json"
echo "Access-Control-Allow-Origin: *"
echo "Access-Control-Allow-Methods: GET, POST"
echo "Access-Control-Allow-Headers: Content-Type"
echo "" # 헤더와 바디 구분용 공백 라인

# --------- 4. URL-encoded 파라미터 파싱 ------------------------------
urldecode() { : "${*//+/ }"; echo -e "${_//%/\\\\x}"; }

declare -A PARAM

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
        CONTENT_LENGTH=${CONTENT_LENGTH:-0}
        if [ "$CONTENT_LENGTH" -gt 0 ]; then
            read -r -n "$CONTENT_LENGTH" POST_DATA
        else
            POST_DATA=""
        fi
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
DRIVE="${PARAM[drive]}"
TEST_TYPE="${PARAM[test_type]}"

log "Request: ACTION=${ACTION}, DRIVE=${DRIVE}, TEST_TYPE=${TEST_TYPE}"

# --------- 5. JSON 응답 함수 ----------------------------------------
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

# --------- 6. 액션 라우팅 -------------------------------------------
_UNIQUE="$(/bin/get_key_value /etc.defaults/synoinfo.conf unique 2>/dev/null || echo 'unknown')"
_BUILD="$(/bin/get_key_value /etc.defaults/VERSION buildnumber 2>/dev/null || echo 'unknown')"

case "${ACTION}" in
    info)
        DATA="\"unique\":\"${_UNIQUE}\",\"build\":\"${_BUILD}\""
        json_response true "System information retrieved" "${DATA}"
        ;;

    scan)
        log "Executing SMART scan operation"
        
        if [ ! -f "${SMART_INFO_SH}" ]; then
            log "[ERROR] SMART script not found: ${SMART_INFO_SH}"
            json_response false "SMART script not found"
            exit 0
        fi
        
        TEMP_LOG="${LOG_DIR}/scan_temp.log"
        RESULT_DIR="/usr/syno/synoman/webman/3rdparty/${PKG_NAME}/result"
        mkdir -p "${RESULT_DIR}"
        
        log "[DEBUG] Executing: ${SMART_INFO_SH}"
        timeout 120 "${SMART_INFO_SH}" > "${TEMP_LOG}" 2>&1
        EXIT_CODE=$?
        
        if [ ${EXIT_CODE} -eq 0 ]; then
            log "[SUCCESS] SMART scan completed"
            # 결과 파일을 웹에서 접근 가능한 위치에 복사
            cp "${TEMP_LOG}" "${RESULT_DIR}/smart.result"
            chmod 644 "${RESULT_DIR}/smart.result"
            json_response true "SMART scan completed successfully"
        elif [ ${EXIT_CODE} -eq 124 ]; then
            log "SMART scan timed out after 120 seconds"
            json_response false "SMART scan failed: Operation timed out after 120 seconds"
        else
            log "SMART scan failed with exit code: ${EXIT_CODE}"
            ERR="$(tail -n 5 "${TEMP_LOG}" 2>/dev/null | head -n 1 || echo 'Unknown error')"
            json_response false "SMART scan failed: ${ERR}"
        fi
        
        rm -f "${TEMP_LOG}"
        ;;

    health)
        log "Executing health check operation"
        
        if [ -z "${DRIVE}" ]; then
            log "[ERROR] Missing parameter: DRIVE"
            json_response false "Missing parameter: drive"
            exit 0
        fi
        
        # 드라이브 경로 검증
        if [[ ! "${DRIVE}" =~ ^[a-zA-Z0-9_-]+$ ]]; then
            log "[ERROR] Invalid drive parameter: ${DRIVE}"
            json_response false "Invalid drive parameter: ${DRIVE}"
            exit 0
        fi
        
        TEMP_LOG="${LOG_DIR}/health_temp.log"
        log "[DEBUG] Executing health check for drive: ${DRIVE}"
        
        # smartctl 명령어 찾기
        SMARTCTL_CMD=""
        if command -v smartctl7 >/dev/null 2>&1; then
            SMARTCTL_CMD="smartctl7"
        elif command -v smartctl >/dev/null 2>&1; then
            SMARTCTL_CMD="smartctl"
        else
            json_response false "smartctl command not available"
            exit 0
        fi
        
        # 드라이브 존재 확인
        if [ ! -e "/dev/${DRIVE}" ]; then
            json_response false "Drive /dev/${DRIVE} not found"
            exit 0
        fi
        
        timeout 30 "${SMARTCTL_CMD}" -H -d sat -T permissive "/dev/${DRIVE}" > "${TEMP_LOG}" 2>&1
        EXIT_CODE=$?
        
        if [ ${EXIT_CODE} -eq 0 ] || [ ${EXIT_CODE} -eq 4 ]; then
            # smartctl은 정상적인 경우에도 exit code 4를 반환할 수 있음
            log "[SUCCESS] Health check completed for drive: ${DRIVE}"
            HEALTH_RESULT="$(cat "${TEMP_LOG}" | head -20)"  # 결과를 20줄로 제한
            json_response true "Health check completed" "\"drive\":\"${DRIVE}\",\"result\":\"${HEALTH_RESULT//\"/\\\"}\""
        else
            log "Health check failed for drive: ${DRIVE} with exit code: ${EXIT_CODE}"
            ERR="$(cat "${TEMP_LOG}" | head -5)"
            json_response false "Health check failed for drive ${DRIVE}: ${ERR//\"/\\\"}"
        fi
        
        rm -f "${TEMP_LOG}"
        ;;

    test)
        log "Executing SMART test operation"
        
        if [ -z "${DRIVE}" ]; then
            log "[ERROR] Missing parameter: DRIVE"
            json_response false "Missing parameter: drive"
            exit 0
        fi
        
        if [ -z "${TEST_TYPE}" ]; then
            TEST_TYPE="short"
        fi
        
        # 테스트 타입 검증
        case "${TEST_TYPE}" in
            short|long|conveyance)
                ;;
            *)
                log "[ERROR] Invalid test type: ${TEST_TYPE}"
                json_response false "Invalid test type: ${TEST_TYPE}. Use short, long, or conveyance"
                exit 0
                ;;
        esac
        
        # smartctl 명령어 찾기
        SMARTCTL_CMD=""
        if command -v smartctl7 >/dev/null 2>&1; then
            SMARTCTL_CMD="smartctl7"
        elif command -v smartctl >/dev/null 2>&1; then
            SMARTCTL_CMD="smartctl"
        else
            json_response false "smartctl command not available"
            exit 0
        fi
        
        # 드라이브 존재 확인
        if [ ! -e "/dev/${DRIVE}" ]; then
            json_response false "Drive /dev/${DRIVE} not found"
            exit 0
        fi
        
        TEMP_LOG="${LOG_DIR}/test_temp.log"
        log "[DEBUG] Starting ${TEST_TYPE} test for drive: ${DRIVE}"
        
        "${SMARTCTL_CMD}" -t "${TEST_TYPE}" -d sat "/dev/${DRIVE}" > "${TEMP_LOG}" 2>&1
        EXIT_CODE=$?
        
        if [ ${EXIT_CODE} -eq 0 ]; then
            log "[SUCCESS] ${TEST_TYPE} test started for drive: ${DRIVE}"
            json_response true "${TEST_TYPE} test started successfully for drive: ${DRIVE}"
        else
            log "${TEST_TYPE} test failed to start for drive: ${DRIVE}"
            ERR="$(head -5 "${TEMP_LOG}")"
            json_response false "Failed to start ${TEST_TYPE} test: ${ERR//\"/\\\"}"
        fi
        
        rm -f "${TEMP_LOG}"
        ;;

    generate)
        log "Executing generate result operation"
        
        if [ ! -f "${GENERATE_RESULT_SH}" ]; then
            log "[ERROR] Generate script not found: ${GENERATE_RESULT_SH}"
            json_response false "Generate script not found"
            exit 0
        fi
        
        TEMP_LOG="${LOG_DIR}/generate_temp.log"
        log "[DEBUG] Executing: ${GENERATE_RESULT_SH}"
        
        timeout 60 "${GENERATE_RESULT_SH}" > "${TEMP_LOG}" 2>&1
        EXIT_CODE=$?
        
        if [ ${EXIT_CODE} -eq 0 ]; then
            log "[SUCCESS] Result generation completed"
            json_response true "SMART result generated successfully"
        elif [ ${EXIT_CODE} -eq 124 ]; then
            log "Result generation timed out"
            json_response false "Result generation failed: Operation timed out"
        else
            log "Result generation failed with exit code: ${EXIT_CODE}"
            ERR="$(tail -n 3 "${TEMP_LOG}" 2>/dev/null | head -n 1 || echo 'Unknown error')"
            json_response false "Result generation failed: ${ERR}"
        fi
        
        rm -f "${TEMP_LOG}"
        ;;

    *)
        log "[ERROR] Invalid action: ${ACTION}"
        json_response false "Invalid action: ${ACTION}"
        ;;
esac
