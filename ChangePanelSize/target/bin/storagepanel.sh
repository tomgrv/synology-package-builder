#!/usr/bin/env bash
#
# Storage Panel Manager - Package Version
# GUI Package wrapper for storage panel modification
#

HDD_BAY_LIST=(RACK_0_Bay RACK_2_Bay RACK_4_Bay RACK_8_Bay RACK_10_Bay RACK_12_Bay RACK_12_Bay_2 RACK_16_Bay RACK_20_Bay RACK_24_Bay RACK_60_Bay TOWER_1_Bay TOWER_2_Bay TOWER_4_Bay TOWER_4_Bay_J TOWER_4_Bay_S TOWER_5_Bay TOWER_6_Bay TOWER_8_Bay TOWER_12_Bay)

# Logging function
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> /var/log/storagepanel.log
}

log_message "Storage Panel Manager called with parameters: $*"

if [ "${1}" = "-h" ]; then
  echo "Storage Panel Manager - Package Version"
  echo "Use: ${0} [HDD_BAY [SSD_BAY]]"
  echo "  HDD_BAY: ${HDD_BAY_LIST[@]}"
  echo "  SSD_BAY: (row)X(column)"
  echo "  -r: restore"
  echo "  -h: help"
  exit 0
fi

_UNIQUE="$(/bin/get_key_value /etc.defaults/synoinfo.conf unique)"
_BUILD="$(/bin/get_key_value /etc.defaults/VERSION buildnumber)"

log_message "System Info - Unique: $_UNIQUE, Build: $_BUILD"

if [ ${_BUILD:-64570} -gt 64570 ]; then
  FILE_JS="/usr/local/packages/@appstore/StorageManager/ui/storage_panel.js"
else
  FILE_JS="/usr/syno/synoman/webman/modules/StorageManager/storage_panel.js"
fi
FILE_GZ="${FILE_JS}.gz"

# 파일 존재 여부 확인 및 권한 검사
check_file_permissions() {
    local file="$1"
    if [ ! -f "$file" ]; then
        log_message "ERROR: File does not exist: $file"
        return 1
    fi
    if [ ! -w "$file" ]; then
        log_message "ERROR: File is not writable: $file"
        return 1
    fi
    return 0
}

# JS 파일 존재 여부 확인
log_message "Checking files: FILE_JS=${FILE_JS}, FILE_GZ=${FILE_GZ}"
if ! check_file_permissions "${FILE_JS}"; then
    echo "ERROR: Cannot access ${FILE_JS}"
    exit 1
fi

# Create compressed version if it doesn't exist
if [ -f "${FILE_JS}" -a ! -f "${FILE_GZ}" ]; then
    log_message "Creating gzip file: ${FILE_GZ}"
    if ! gzip -c "${FILE_JS}" > "${FILE_GZ}"; then
        log_message "ERROR: Failed to create gzip file"
        echo "ERROR: Failed to create ${FILE_GZ}"
        exit 1
    fi
fi

# gz 파일 존재 여부 확인
if ! check_file_permissions "${FILE_GZ}"; then
    echo "ERROR: Cannot access ${FILE_GZ}"
    exit 1
fi

# Restore function
if [ "${1}" = "-r" ]; then
  if [ -f "${FILE_GZ}.bak" ]; then
    mv -f "${FILE_GZ}.bak" "${FILE_GZ}"
    gzip -dc "${FILE_GZ}" >"${FILE_JS}"
    log_message "Configuration restored successfully"
    echo "Configuration restored successfully"
  else
    log_message "ERROR: No backup file found"
    echo "ERROR: No backup file found"
    exit 1
  fi
  exit 0
fi

# Validate parameters
HDD_BAY="${1}"
if [ -n "${1}" ] && ! echo "${HDD_BAY_LIST[@]}" | grep -wq "${1}"; then
  log_message "ERROR: Invalid HDD_BAY parameter: ${1}"
  echo "ERROR: Invalid HDD_BAY parameter: ${1}"
  exit 1
fi

SSD_BAY="${2}"
if [ -n "${2}" ] && [ -z "$(echo "${2}" | sed -n '/^[0-9]\{1,2\}X[0-9]\{1,2\}$/p')" ]; then
  log_message "ERROR: Invalid SSD_BAY parameter: ${2}"
  echo "ERROR: Invalid SSD_BAY parameter: ${2}"
  exit 1
fi

# Auto-detect if parameters not provided
if [ -z "${HDD_BAY}" ]; then
  IDX="$(echo $(synodisk --enum -t internal 2>/dev/null | grep "Disk id:" | tail -n 1 | cut -d: -f2))"
  IDX=${IDX:-0}
  while [ ${IDX} -le 60 ]; do
    for i in "${HDD_BAY_LIST[@]}"; do
      echo "${i}" | grep -q "_${IDX}_" && HDD_BAY="${i}" && break 2
    done
    IDX=$((IDX + 1))
  done
  HDD_BAY=${HDD_BAY:-RACK_60_Bay}
  log_message "Auto-detected HDD_BAY: ${HDD_BAY}"
fi

if [ -z "${SSD_BAY}" ]; then
  IDX="$(echo $(synodisk --enum -t cache 2>/dev/null | grep "Disk id:" | tail -n 1 | cut -d: -f2))"
  SSD_BAY="$((${IDX:-0} / 8 + 1))X8"
  log_message "Auto-detected SSD_BAY: ${SSD_BAY}"
fi

# Create backup if it doesn't exist
[ ! -f "${FILE_GZ}.bak" ] && cp -f "${FILE_GZ}" "${FILE_GZ}.bak"

# Apply configuration
gzip -dc "${FILE_GZ}" >"${FILE_JS}"
log_message "Setting storage panel to ${HDD_BAY} ${SSD_BAY}"

OLD="driveShape:\"Mdot2-shape\",major:\"row\",rowDir:\"UD\",colDir:\"LR\",driveSection:\[{top:14,left:18,rowCnt:[0-9]\+,colCnt:[0-9]\+,xGap:6,yGap:6}\]},"
NEW="driveShape:\"Mdot2-shape\",major:\"row\",rowDir:\"UD\",colDir:\"LR\",driveSection:\[{top:14,left:18,rowCnt:${SSD_BAY%%X*},colCnt:${SSD_BAY##*X},xGap:6,yGap:6}\]},"

# 파일 내용 백업
log_message "Creating backup of current content"
cp "${FILE_JS}" "${FILE_JS}.bak.$(date +%s)"

# sed 명령 실행 및 결과 확인
log_message "Applying changes with sed..."
log_message "HDD_BAY=${HDD_BAY}, _UNIQUE=${_UNIQUE}"
if ! sed -i "s/\"${_UNIQUE}\",//g; s/,\"${_UNIQUE}\"//g; s/${HDD_BAY}:\[\"/${HDD_BAY}:\[\"${_UNIQUE}\",\"/g; s/M2X1:\[\"/M2X1:\[\"${_UNIQUE}\",\"/g; s/${OLD}/${NEW}/g" "${FILE_JS}"; then
    log_message "ERROR: sed command failed"
    echo "ERROR: Failed to modify ${FILE_JS}"
    exit 1
fi

# 변경사항 확인
log_message "Checking if changes were applied..."
if ! grep -q "${HDD_BAY}:\[\"${_UNIQUE}\"" "${FILE_JS}"; then
    log_message "ERROR: Changes were not applied correctly"
    log_message "Content after sed: $(grep -A 1 "${HDD_BAY}" "${FILE_JS}")"
    # 백업에서 복구
    mv "${FILE_JS}.bak.$(date +%s)" "${FILE_JS}"
    echo "ERROR: Changes were not applied correctly"
    exit 1
fi

# gzip 파일 업데이트
log_message "Updating gzip file..."
if ! gzip -c "${FILE_JS}" > "${FILE_GZ}.tmp" || ! mv "${FILE_GZ}.tmp" "${FILE_GZ}"; then
    log_message "ERROR: Failed to update gzip file"
    echo "ERROR: Failed to update ${FILE_GZ}"
    exit 1
fi

log_message "Storage panel configuration applied successfully: ${HDD_BAY} ${SSD_BAY}"
echo "Storage panel set to ${HDD_BAY} ${SSD_BAY}"

exit 0