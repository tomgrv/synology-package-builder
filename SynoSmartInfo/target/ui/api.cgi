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

# --------- 7. 시스템 정보 수집 함수 ----------------------------------
get_system_info() {
    local unique build model version
    
    # 안전한 기본값 설정
    unique="unknown"
    build="unknown"
    model="unknown"
    version="unknown"
    
    # 시스템 정보 수집 (오류 시 기본값 유지)
    if [ -f "/etc.defaults/synoinfo.conf" ]; then
        unique="$(/bin/get_key_value /etc.defaults/synoinfo.conf unique 2>/dev/null || echo 'unknown')"
    fi
    
    if [ -f "/etc.defaults/VERSION" ]; then
        build="$(/bin/get_key_value /etc.defaults/VERSION buildnumber 2>/dev/null || echo 'unknown')"
    fi
    
    if [ -f "/proc/sys/kernel/syno_hw_version" ]; then
        model="$(cat /proc/sys/kernel/syno_hw_version 2>/dev/null || echo 'unknown')"
    fi
    
    # DSM 버전 정보
    local productversion buildphase smallfixnumber
    if command -v /usr/syno/bin/synogetkeyvalue >/dev/null 2>&1; then
        productversion="$(/usr/syno/bin/synogetkeyvalue /etc.defaults/VERSION productversion 2>/dev/null || echo 'unknown')"
        buildphase="$(/usr/syno/bin/synogetkeyvalue /etc.defaults/VERSION buildphase 2>/dev/null || echo '')"
        smallfixnumber="$(/usr/syno/bin/synogetkeyvalue /etc.defaults/VERSION smallfixnumber 2>/dev/null || echo '')"
        
        if [ "$buildphase" != "" ] && [ "$smallfixnumber" != "" ]; then
            version="${productversion}-${build}-${buildphase}-${smallfixnumber}"
        else
            version="${productversion}-${build}"
        fi
    fi
    
    # 각 값들을 JSON 이스케이프 처리
    unique="$(json_escape "$unique")"
    build="$(json_escape "$build")"
    model="$(json_escape "$model")"
    version="$(json_escape "$version")"
    
    echo "\"unique\":\"${unique}\",\"build\":\"${build}\",\"model\":\"${model}\",\"version\":\"${version}\""
}

# --------- 8. 액션 처리 -------------------------------------------
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
                json_response false "허용되지 않은 옵션입니다: ${OPTION}"
                exit 0
                ;;
        esac
        
        if [ ! -x "${SMART_INFO_SH}" ]; then
            json_response false "SMART 스크립트가 없거나 실행 권한이 없습니다."
            exit 0
        fi

        # 옵션에 따른 로그 메시지
        if [ -z "${OPTION}" ]; then
            log "[DEBUG] Executing SMART script with default options (no parameters)"
            OPTION_DESC="기본 검사"
        else
            log "[DEBUG] Executing SMART script with option: ${OPTION}"
            OPTION_DESC="옵션 ${OPTION}"
        fi
        
        # SMART 스크립트 실행
        TEMP_RESULT="${LOG_DIR}/temp_smart_result.txt"
        
        # 옵션이 있으면 전달, 없으면 기본 실행
        if [ -z "${OPTION}" ]; then
            timeout 120 "${SMART_INFO_SH}" > "${TEMP_RESULT}" 2>&1
        else
            timeout 120 "${SMART_INFO_SH}" "${OPTION}" > "${TEMP_RESULT}" 2>&1
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
                json_response true "SMART 검사가 성공적으로 완료되었습니다 (${OPTION_DESC})" "\"result\":\"${ESCAPED_RESULT}\""
            else
                # 결과 파일이 없거나 읽을 수 없는 경우 임시 결과 사용
                SMART_RESULT="$(cat "${TEMP_RESULT}" 2>/dev/null | head -50)"
                ESCAPED_RESULT="$(json_escape "$SMART_RESULT")"
                json_response true "SMART 검사가 완료되었습니다 (결과 파일 생성 실패)" "\"result\":\"${ESCAPED_RESULT}\""
            fi
            
        elif [ ${RET} -eq 124 ]; then
            log "[ERROR] SMART script execution timed out"
            json_response false "SMART 검사 시간 초과 (120초)" "\"result\":\"Script execution timed out after 120 seconds\""
        else
            log "[ERROR] SMART script execution failed with code: ${RET}"
            # 오류 내용도 읽어서 반환
            ERROR_RESULT="$(cat "${TEMP_RESULT}" 2>/dev/null | head -20)"
            ESCAPED_ERROR="$(json_escape "$ERROR_RESULT")"
            json_response false "SMART 검사 실행 실패 (코드: ${RET})" "\"result\":\"${ESCAPED_ERROR}\""
        fi
        
        # 임시 파일 정리
        rm -f "${TEMP_RESULT}"
        ;;

    *)
        log "[ERROR] Invalid action: ${ACTION}"
        json_response false "Invalid action: ${ACTION}"
        ;;
esac
