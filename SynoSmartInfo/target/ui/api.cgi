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

# --------- 2. 디렉터리 및 권한 준비 -----------------------------------
mkdir -p "${LOG_DIR}"
touch "${LOG_FILE}"
chmod 644 "${LOG_FILE}"

chmod +x "${SMART_INFO_SH}" 2>/dev/null || echo "[ERROR] Failed to chmod ${SMART_INFO_SH}" >> "${LOG_FILE}"

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
OPTION="${PARAM[option]}"

log "Request: ACTION=${ACTION}, OPTION=${OPTION}"

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

# --------- 6. 액션 처리 -------------------------------------------
case "${ACTION}" in
    run)
        # 허용 옵션만 처리
        case "${OPTION}" in
            -a|-e|-h|-v|-d)
                ;;
            *)
                json_response false "허용되지 않은 옵션입니다: ${OPTION}"
                exit 0
                ;;
        esac
        
        if [ ! -x "${SMART_INFO_SH}" ]; then
            json_response false "실행할 스크립트가 없거나 실행 권한이 없습니다."
            exit 0
        fi

        # 옵션을 인자로 넘겨 실행, 실행 결과 캡처
        RESULT=$("${SMART_INFO_SH}" "${OPTION}" 2>&1)
        RET=$?

        if [ ${RET} -eq 0 ]; then
            json_response true "스크립트 실행 성공" "\"result\":\"$(echo "${RESULT}" | sed 's/"/\\"/g')\""
        else
            json_response false "스크립트 실행 실패 (코드: ${RET})" "\"result\":\"$(echo "${RESULT}" | sed 's/"/\\"/g')\""
        fi
        ;;

    *)
        log "[ERROR] Invalid action: ${ACTION}"
        json_response false "Invalid action: ${ACTION}"
        ;;
esac
