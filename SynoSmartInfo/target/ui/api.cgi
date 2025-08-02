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
echo "Content-Type: application/json; charset=utf-8"
echo "Access-Control-Allow-Origin: *"
echo "Access-Control-Allow-Methods: GET, POST"
echo "Access-Control-Allow-Headers: Content-Type"
echo ""  # 헤더와 바디 구분용 공백 라인

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

log "Request: ACTION=${ACTION}, OPTION=[${OPTION}]"

# --------- 5. JSON 문자열 이스케이프 함수 ----------------------------
json_escape() {
    sed ':a;N;$!ba;s/\\/\\\\/g; s/"/\\"/g; s/\r//g; s/\n/\\n/g; s/\t/\\t/g;'
}

# --------- 6. JSON 응답 함수 ----------------------------------------
json_response() {
    local success="$1" message="$2" data="$3"
    local escaped_message
    local json_output
    
    escaped_message="$(printf '%s' "$message" | json_escape)"
    
    # JSON 문자열을 변수에 저장
    json_output="{"
    json_output+="\"success\": ${success},"
    json_output+="\"message\": \"${escaped_message}\""
    if [ -n "${data}" ]; then
        json_output+=",${data}"
    fi
    json_output+="}"
    
    # 로그 파일에 JSON 응답 저장 (원하는 로그 함수 또는 직접 echo)
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] JSON_RESPONSE: $json_output" >> "${LOG_FILE}"
    
    # 실제 JSON 응답 출력
    echo "$json_output"
}


# --------- 7. 문자열 정제 함수 ----------------------------------------
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

# --------- 8. 시스템 정보 수집 함수 ----------------------------------
get_system_info() {
    local unique build model version

    unique="$(/bin/get_key_value /etc.defaults/synoinfo.conf unique 2>/dev/null || echo '')"
    build="$(/bin/get_key_value /etc.defaults/VERSION buildnumber 2>/dev/null || echo '')"
    model="$(cat /proc/sys/kernel/syno_hw_version 2>/dev/null || echo '')"

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

    unique="$(printf '%s' "$(clean_system_string "$unique")" | json_escape)"
    build="$(printf '%s' "$(clean_system_string "$build")" | json_escape)"
    model="$(printf '%s' "$(clean_system_string "$model")" | json_escape)"
    version="$(printf '%s' "$(clean_system_string "$version")" | json_escape)"

    echo "\"unique\":\"${unique}\",\"build\":\"${build}\",\"model\":\"${model}\",\"version\":\"${version}\""
}

# --------- 9. 액션 처리 -------------------------------------------
case "${ACTION}" in
    info)
        log "[DEBUG] Getting system information"
        DATA="$(get_system_info)"
        json_response true "System information retrieved" "${DATA}"
        ;;

    run)
        case "${OPTION}" in
            ""|"-a"|"-e"|"-h"|"-v"|"-d")
                ;;
            *)
                json_response false "Invalid option: ${OPTION}"
                exit 0
                ;;
        esac
        
        if [ ! -x "${GENERATE_RESULT_SH}" ]; then
            json_response false "Generate script not found or not executable"
            exit 0
        fi

        if [ -z "${OPTION}" ]; then
            log "[DEBUG] Executing generate script with default options (no parameters)"
            OPTION_DESC="default scan"
            timeout 240 sudo "${GENERATE_RESULT_SH}" 2>&1
        else
            log "[DEBUG] Executing generate script with option: ${OPTION}"
            OPTION_DESC="option ${OPTION}"
            timeout 240 sudo "${GENERATE_RESULT_SH}" "${OPTION}" 2>&1
        fi

        RET=$?

        if [ ${RET} -eq 0 ] || [ ${RET} -eq 5 ]; then
            if [ ${RET} -eq 5 ]; then
                log "[PARTIAL SUCCESS] Generate script completed with warnings (code: 5) - ${OPTION_DESC}"
            else
                log "[SUCCESS] Generate script execution completed successfully - ${OPTION_DESC}"
            fi
sleep 3
            if [ -f "${RESULT_FILE}" ] && [ -r "${RESULT_FILE}" ]; then
                SMART_RESULT="$(cat "${RESULT_FILE}" 2>/dev/null)"
log "[SMART_RESULT] : ${SMART_RESULT}"
                ESCAPED_RESULT="$(printf '%s' "$SMART_RESULT" | json_escape)"
log "[ESCAPED_RESULT] : ${ESCAPED_RESULT}"                
                if [ ${RET} -eq 5 ]; then
                    json_response true "SMART scan completed with warnings" "${ESCAPED_RESULT}"
                else
                    json_response true "SMART scan completed successfully" "${ESCAPED_RESULT}"
                fi
            else
                log "[WARNING] Result file not found or not readable: ${RESULT_FILE}"
                json_response false "Result file not available"
            fi

        elif [ ${RET} -eq 124 ]; then
            log "[ERROR] Generate script execution timed out"
            json_response false "SMART scan timed out (240 seconds)" "\"result\":\"Script execution timed out after 240 seconds\""
        else
            log "[ERROR] Generate script execution failed with code: ${RET}"
            json_response false "SMART scan execution failed (code: ${RET})"
        fi
        ;;

    *)
        log "[ERROR] Invalid action: ${ACTION}"
        json_response false "Invalid action: ${ACTION}"
        ;;
esac
