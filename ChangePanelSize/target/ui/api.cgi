#!/bin/bash
###############################################################################
# Storage Panel Manager – CGI API                                            #
# 위치 : @appstore/<패키지명>/ui/api.cgi                                     #
###############################################################################

# ---------- 1. 공통 변수 및 경로 계산 ---------------------------------------
# 현재 스크립트가 위치한 절대경로 (ui 디렉터리)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_ROOT="$(dirname "${SCRIPT_DIR}")"                 # @appstore/<패키지명>
LOG_DIR="${PKG_ROOT}/var"
LOG_FILE="${LOG_DIR}/api.log"
BIN_DIR="${PKG_ROOT}/target/bin"
STORAGE_SH="${BIN_DIR}/storagepanel.sh"

# ---------- 2. 로그 디렉터리 준비 -------------------------------------------
mkdir -p "${LOG_DIR}"
touch "${LOG_FILE}"
chmod 644 "${LOG_FILE}"

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
        if "${STORAGE_SH}" "${HDD_BAY}" "${SSD_BAY}" >> "${LOG_FILE}" 2>&1; then
            json_response true \
                "Configuration applied: ${HDD_BAY} ${SSD_BAY}"
        else
            ERR="$(tail -n 1 "${LOG_FILE}")"
            json_response false "Apply failed: ${ERR}"
        fi
        ;;

    restore)
        if "${STORAGE_SH}" -r >> "${LOG_FILE}" 2>&1; then
            json_response true "Original configuration restored"
        else
            ERR="$(tail -n 1 "${LOG_FILE}")"
            json_response false "Restore failed: ${ERR}"
        fi
        ;;

    *)
        json_response false "Invalid action: ${ACTION}"
        ;;
esac
