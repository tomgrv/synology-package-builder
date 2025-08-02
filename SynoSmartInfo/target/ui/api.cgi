#!/bin/bash
#########################################################################
# Synology SMART Info API – CGI API                                     #
# 위치: @appstore/SynoSmartInfo/ui/api.cgi                              #
#########################################################################

# --------- 1. 공통 변수 및 경로 계산 ---------------------------------
PKG="SynoSmartInfo"
PKG_ROOT="/var/packages/${PKG}"
BIN_DIR="${PKG_ROOT}/target/bin"
LOG_DIR="${PKG_ROOT}/var"
LOG_FILE="${LOG_DIR}/api.log"
RESULT_DIR="/usr/syno/synoman/webman/3rdparty/${PKG}/result"
RESULT_FILE="${RESULT_DIR}/smart.result"
GENERATE_SCRIPT="${BIN_DIR}/generate_smart_result.sh"

# --------- 2. 디렉터리 및 권한 준비 -----------------------------------
mkdir -p "${LOG_DIR}" "${RESULT_DIR}"
touch "${LOG_FILE}"
chmod 644 "${LOG_FILE}"
chmod 755 "${RESULT_DIR}"
chmod +x "${GENERATE_SCRIPT}" 2>/dev/null || echo "[ERROR] chmod ${GENERATE_SCRIPT}" >> "${LOG_FILE}"

log(){ echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${LOG_FILE}"; }

# --------- 3. HTTP 헤더 출력 ----------------------------------------
echo "Content-Type: application/json; charset=utf-8"
echo "Access-Control-Allow-Origin: *"
echo "Access-Control-Allow-Methods: GET, POST"
echo "Access-Control-Allow-Headers: Content-Type"
echo ""

# --------- 4. 파라미터 파싱 ------------------------------------------
read -r BODY
declare -A P
IFS='&' read -r -a KV <<< "$BODY"
for i in "${KV[@]}"; do
  IFS='=' read K V <<< "$i"
  P[$K]="${V}"
done
ACTION="${P[action]}"
OPTION="${P[option]}"

log "Request: ACTION=${ACTION}, OPTION=[${OPTION}]"

# --------- 5. JSON 유틸 ---------------------------------------------
json_escape(){ \
  sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e ':a;N;$!ba;s/\r//g' -e 's/\n/\\n/g'; }
json_response(){
  local ok="$1" msg="$2" data="$3"
  msg=$(printf '%s' "$msg" | json_escape)
  printf '{"success":%s,"message":"%s"' "$ok" "$msg"
  [ -n "$data" ] && printf ',"result":"%s"' "$(printf '%s' "$data" | json_escape)"
  echo "}"
}

# --------- 6. 시스템 정보 (info 액션) -----------------------------
get_system_info(){
  unique=$(/bin/get_key_value /etc.defaults/synoinfo.conf unique 2>/dev/null || echo '')
  build=$(/bin/get_key_value /etc.defaults/VERSION buildnumber 2>/dev/null || echo '')
  model=$(cat /proc/sys/kernel/syno_hw_version 2>/dev/null || echo '')
  product=$(/usr/syno/bin/synogetkeyvalue /etc.defaults/VERSION productversion 2>/dev/null || echo '')
  version="${product}-${build}"
  # Clean 'unknown'
  for v in unique build model version; do
    val=${!v}
    val=${val// unknown/}
    val=${val//unknown/}
    if [ -z "$val" ]; then val="N/A"; fi
    eval "$v=\"\$val\""
  done
  echo "{\"unique\":\"$unique\",\"build\":\"$build\",\"model\":\"$model\",\"version\":\"$version\"}"
}

# --------- 7. ACTION 처리 -------------------------------------------
case "$ACTION" in
  info)
    log "Returning system information"
    SYS_JSON=$(get_system_info)
    printf '{"success":true,"message":"System information retrieved",%s}' "${SYS_JSON}"
    ;;
  run)
    # Validate option
    case "$OPTION" in ""|-a|-e|-h|-v|-d) ;; *)
      json_response false "Invalid option: $OPTION"; exit 0;;
    esac
    # Run generator
    log "Running generate_smart_result.sh option='$OPTION'"
    if sudo "$GENERATE_SCRIPT" "$OPTION"; then
      log "generate_smart_result.sh completed"
    else
      log "generate_smart_result.sh failed"
      json_response false "Generate script execution failed"; exit 0
    fi
    # Copy result
    if [ -f "${PKG_ROOT}/target/bin/smart.result" ]; then
      cp "${PKG_ROOT}/target/bin/smart.result" "$RESULT_FILE" 2>/dev/null
      chmod 644 "$RESULT_FILE"
      log "Copied smart.result to web folder"
    fi
    # Return result
    if [ -r "$RESULT_FILE" ]; then
      RESULT=$(<"$RESULT_FILE")
      json_response true "SMART scan completed" "$RESULT"
    else
      json_response false "Result file not available"
    fi
    ;;
  *)
    log "Invalid action: $ACTION"
    json_response false "Invalid action: $ACTION"
    ;;
esac
