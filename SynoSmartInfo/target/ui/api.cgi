#!/bin/bash

#########################################################################
# Synology SMART Info API - CGI API                                     #
# 위치: @appstore/SynoSmartInfo/ui/api.cgi                              #
#########################################################################

# --------- 1. 공통 변수 및 경로 계산 ---------------------------------
PKG_NAME="Synosmartinfo"
PKG_ROOT="/var/packages/${PKG_NAME}"
TARGET_DIR="${PKG_ROOT}/target"
LOG_DIR="${PKG_ROOT}/var"
LOG_FILE="${LOG_DIR}/api.log"
BIN_DIR="${TARGET_DIR}/bin"
GENERATE_RESULT_SH="${BIN_DIR}/generate_smart_result.sh"
RESULT_DIR="/usr/syno/synoman/webman/3rdparty/${PKG_NAME}/result"
RESULT_FILE="${RESULT_DIR}/smart.result"

# --------- 2. 디렉터리 및 권한 준비 -----------------------------------
mkdir -p "${LOG_DIR}"
mkdir -p "${RESULT_DIR}"
touch "${LOG_FILE}"
chmod 644 "${LOG_FILE}"
chmod 755 "${RESULT_DIR}"

chmod +x "${GENERATE_RESULT_SH}" 2>/dev/null || echo "[ERROR] Failed to chmod ${GENERATE_RESULT_SH}" >> "${LOG_FILE}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${LOG_FILE}"
}

# --------- 3. HTTP 헤더 출력 ----------------------------------------
echo "Content-Type: text/plain; charset=utf-8"
echo "Access-Control-Allow-Origin: *"
echo "Access-Control-Allow-Methods: GET, POST"
echo "Access-Control-Allow-Headers: Content-Type"
echo ""  # 헤더와 바디 구분용 공백 라인

# --------- 4. URL-encoded 파라미터 파싱 ------------------------------
urldecode() { : "${*//+/ }"; echo -e "${_//%/\\x}"; }

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
        echo "ERROR: Unsupported METHOD"
        exit 0
        ;;
esac

ACTION="${PARAM[action]}"
OPTION="${PARAM[option]}"

log "Request: ACTION=${ACTION}, OPTION=[${OPTION}]"

# --------- 5. TEXT 응답 함수 ----------------------------------------
text_response() {
    local ok="$1" msg="$2" data="$3"
    if [ "$ok" = "true" ]; then
        echo "SUCCESS: $msg"
    else
        echo "ERROR: $msg"
    fi
    [ -n "$data" ] && printf "DATA_START\n%s\nDATA_END\n" "$data"
}

# --------- 6. 문자열 정제 함수 ----------------------------------------
clean_system_string() {
    local input="$1"
    input=$(echo "$input" | sed 's/ unknown//g' | sed 's/unknown //g' | sed 's/^unknown$//')
    input=$(echo "$input" | sed 's/  */ /g' | sed 's/^ *//' | sed 's/ *$//')
    if [ -z "$input" ] || [ "$input" = " " ]; then
        echo "N/A"
    else
        echo "$input"
    fi
}

# --------- 7. 시스템 정보 수집 함수 ----------------------------------
get_system_info() {
    local unique build model version

    model="$(cat /proc/sys/kernel/syno_hw_version 2>/dev/null || echo '')"
    platform="$(/bin/get_key_value /etc.defaults/synoinfo.conf platform_name 2>/dev/null || echo '')"

    local productversion
    if command -v /usr/syno/bin/synogetkeyvalue >/dev/null 2>&1; then
        productversion="$(/usr/syno/bin/synogetkeyvalue /etc.defaults/VERSION productversion 2>/dev/null || echo '')"
        if [ -n "$productversion" ] && [ -n "$build" ]; then
            version="${productversion}-${build}"
            version=$(echo "$version" | sed 's/ unknown.*$//' | sed 's/unknown.*$//')
        else
            version=""
        fi
    else
        version=""
    fi

    smallfix="$(/bin/get_key_value /etc/VERSION smallfixnumber 2>/dev/null || echo '')"

    model="$(clean_system_string "$model")"
    platform="$(clean_system_string "$platform")"
    version="$(clean_system_string "$version")"
    smallfix="$(clean_system_string "$smallfix")"

    echo -e "MODEL: ${model}\nPLATFORM: ${platform}\nDSM_VERSION: ${version}\nUpdate: ${smallfix}"
}

# --------- 8. 액션 처리 -------------------------------------------
case "${ACTION}" in
    info)
        log "[DEBUG] Getting system information"
        DATA="$(get_system_info)"
        text_response true "System information retrieved" "${DATA}"
        ;;

    run)
        case "${OPTION}" in
            ""|"-a"|"-e"|"-h"|"-v"|"-d")
                ;;
            *)
                text_response false "Invalid option: ${OPTION}"
                exit 0
                ;;
        esac

        if [ ! -x "${GENERATE_RESULT_SH}" ]; then
            text_response false "Generate script not found or not executable"
            exit 0
        fi

        log "[DEBUG] Executing generate script (option: ${OPTION_DESC:-default scan})"
        timeout 240 sudo "${GENERATE_RESULT_SH}" ${OPTION:+ "$OPTION"} 2>&1
        RET=$?

        # 결과 파일 존재 여부로 성공/실패 판단
        if [ -f "${RESULT_FILE}" ] && [ -s "${RESULT_FILE}" ]; then
            log "[SUCCESS] SMART scan result file exists - ${OPTION_DESC:-default scan}"
            SMART_RESULT="$(cat "${RESULT_FILE}" 2>/dev/null)"
            text_response true "SMART scan completed" "${SMART_RESULT}"
        elif [ ${RET} -eq 124 ]; then
            log "[ERROR] Generate script execution timed out"
            text_response false "SMART scan timed out (240 seconds)" "Script execution timed out after 240 seconds"
        else
            log "[ERROR] Generate script execution failed (code: ${RET})"
            text_response false "SMART scan execution failed (code: ${RET})"
        fi
        ;;

    *)
        log "[ERROR] Invalid action: ${ACTION}"
        text_response false "Invalid action: ${ACTION}"
        ;;
esac
