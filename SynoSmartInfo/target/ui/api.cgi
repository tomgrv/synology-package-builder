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
RESULT_DIR="/usr/syno/synoman/webman/3rdparty/${PKG_NAME}/result"
RESULT_FILE="${RESULT_DIR}/smart.result"

# --------- 2. 디렉터리 및 권한 준비 -----------------------------------
mkdir -p "${LOG_DIR}"
mkdir -p "${RESULT_DIR}"
touch "${LOG_FILE}"
chmod 644 "${LOG_FILE}"
chmod 755 "${RESULT_DIR}"

chmod +x "${SMART_INFO_SH}" 2>/dev/null || echo "[ERROR] Failed to chmod ${SMART_INFO_SH}" >> "${LOG_FILE}"
chmod +x "${GENERATE_RESULT_SH}" 2>/dev/null || echo "[ERROR] Failed to chmod ${GENERATE_RESULT_SH}" >> "${LOG_FILE}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${LOG_FILE}"
}

# --------- 3. HTTP 헤더 출력 ----------------------------------------
echo "Content-Type: application/json; charset=utf-8"
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

log "Request: ACTION=${ACTION}, OPTION=[${OPTION}]"

# --------- 5. JSON 문자열 이스케이프 함수 ----------------------------
json_escape() {
    local input="$1"
    # 백슬래시와 따옴표 이스케이프
    input="${input//\\/\\\\}"
    input="${input//\"/\\\"}"
    # 제어 문자 이스케이프
    input="${input//$'\n'/\\n}"
    input="${input//$'\r'/\\r}"
    input="${input//$'\t'/\\t}"
    input="${input//$'\b'/\\b}"
    input="${input//$'\f'/\\f}"
    # 기타 제어 문자 제거
    input=$(echo "$input" | tr -d '\000-\037\177')
    echo "$input"
}

# --------- 6. JSON 응답 함수 ----------------------------------------
json_response() {
    local success="$1" message="$2" data="$3"
    local escaped_message
    
    escaped_message="$(json_escape "$message")"
    
    {
        echo "{"
        echo "  \"success\": ${success},"
        echo "  \"message\": \"${escaped_message}\""
        if [ -n "${data}" ]; then
            echo "  ,${data}"
        fi
        echo "}"
    }
}

# --------- 7. 문자열 정제 함수 ----------------------------------------
clean_system_string() {
    local input="$1"
    # 'unknown' 문자열과 그 주변 공백 제거
    input=$(echo "$input" | sed 's/ unknown//g' | sed 's/unknown //g' | sed 's/^unknown$//')
    # 연속된 공백을 하나로 변경
    input=$(echo "$input" | sed 's/  */ /g' | sed 's/^ *//' | sed 's/ *$//')
    # 빈 문자열이면 'N/A' 반환
    if [ -z "$input" ] || [ "$input" = " " ]; then
        echo "N/A"
    else
        echo "$input"
    fi
}

# --------- 8. 시스템 정보 수집 함수 ----------------------------------
get_system_info() {
    local unique build model version
    
    # 시스템 정보 수집
    unique="$(/bin/get_key_value /etc.defaults/synoinfo.conf unique 2>/dev/null || echo '')"
    build="$(/bin/get_key_value /etc.defaults/VERSION buildnumber 2>/dev/null || echo '')"
    model="$(cat /proc/sys/kernel/syno_hw_version 2>/dev/null || echo '')"
    
    # DSM 버전 정보
    local productversion
    if command -v /usr/syno/bin/synogetkeyvalue >/dev/null 2>&1; then
        productversion="$(/usr/syno/bin/synogetkeyvalue /etc.defaults/VERSION productversion 2>/dev/null || echo '')"
        if [ -n "$productversion" ] && [ -n "$build" ]; then
            version="${productversion}-${build}"
            # 'unknown' 이후의 모든 문자 제거
            version=$(echo "$version" | sed 's/ unknown.*$//' | sed 's/unknown.*$//')
        else
            version=""
        fi
    else
        version=""
    fi
    
    # 각 값들을 정제 및 JSON 이스케이프 처리
    unique="$(json_escape "$(clean_system_string "$unique")")"
    build="$(json_escape "$(clean_system_string "$build")")"  
    model="$(json_escape "$(clean_system_string "$model")")"
    version="$(json_escape "$(clean_system_string "$version")")"
    
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
        # 허용 옵션 처리 (빈 값도 허용)
        case "${OPTION}" in
            ""|"-a"|"-e"|"-h"|"-v"|"-d")
                ;;
            *)
                json_response false "Invalid option: ${OPTION}"
                exit 0
                ;;
        esac
        
        if [ ! -x "${SMART_INFO_SH}" ]; then
            json_response false "SMART script not found or not executable"
            exit 0
        fi

        # 옵션에 따른 로그 메시지
        if [ -z "${OPTION}" ]; then
            log "[DEBUG] Executing SMART script with default options (no parameters)"
            OPTION_DESC="default scan"
        else
            log "[DEBUG] Executing SMART script with option: ${OPTION}"
            OPTION_DESC="option ${OPTION}"
        fi
        
        # SMART 스크립트 실행 (sudo 권한으로)
        TEMP_RESULT="${LOG_DIR}/temp_smart_result.txt"
        
        # sudo 권한으로 스크립트 실행
        if [ -z "${OPTION}" ]; then
            timeout 120 sudo "${SMART_INFO_SH}" > "${TEMP_RESULT}" 2>&1
        else
            timeout 120 sudo "${SMART_INFO_SH}" "${OPTION}" > "${TEMP_RESULT}" 2>&1
        fi
        RET=$?

        if [ ${RET} -eq 0 ]; then
            log "[SUCCESS] SMART script execution completed successfully with ${OPTION_DESC}"
            
            # 결과를 웹 접근 가능한 위치에 복사
            if cp "${TEMP_RESULT}" "${RESULT_FILE}" 2>/dev/null; then
                chmod 644 "${RESULT_FILE}"
                log "[SUCCESS] Result file created at ${RESULT_FILE}"
            else
                log "[WARNING] Failed to copy result to web directory"
            fi
            
            # 결과 파일 내용 읽기
            if [ -f "${RESULT_FILE}" ] && [ -r "${RESULT_FILE}" ]; then
                SMART_RESULT="$(cat "${RESULT_FILE}" 2>/dev/null | head -100)"  # 처음 100줄만
                ESCAPED_RESULT="$(json_escape "$SMART_RESULT")"
                json_response true "SMART scan completed successfully (${OPTION_DESC})" "\"result\":\"${ESCAPED_RESULT}\""
            else
                # 결과 파일이 없거나 읽을 수 없는 경우 임시 결과 사용
                SMART_RESULT="$(cat "${TEMP_RESULT}" 2>/dev/null | head -50)"
                ESCAPED_RESULT="$(json_escape "$SMART_RESULT")"
                json_response true "SMART scan completed (result file creation failed)" "\"result\":\"${ESCAPED_RESULT}\""
            fi
            
        elif [ ${RET} -eq 124 ]; then
            log "[ERROR] SMART script execution timed out"
            json_response false "SMART scan timed out (120 seconds)" "\"result\":\"Script execution timed out after 120 seconds\""
        else
            log "[ERROR] SMART script execution failed with code: ${RET}"
            # 오류 내용도 읽어서 반환
            ERROR_RESULT="$(cat "${TEMP_RESULT}" 2>/dev/null | head -20)"
            ESCAPED_ERROR="$(json_escape "$ERROR_RESULT")"
            json_response false "SMART scan execution failed (code: ${RET})" "\"result\":\"${ESCAPED_ERROR}\""
        fi
        
        # 임시 파일 정리
        rm -f "${TEMP_RESULT}"
        ;;

    *)
        log "[ERROR] Invalid action: ${ACTION}"
        json_response false "Invalid action: ${ACTION}"
        ;;
esac
