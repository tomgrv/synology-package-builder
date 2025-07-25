#!/usr/bin/env bash
#
# Storage Panel Manager - Package Version
# GUI Package wrapper for storage panel modification
#

HDD_BAY_LIST=(RACK_0_Bay RACK_2_Bay RACK_4_Bay RACK_8_Bay RACK_10_Bay RACK_12_Bay RACK_12_Bay_2 RACK_16_Bay RACK_20_Bay RACK_24_Bay RACK_60_Bay TOWER_1_Bay TOWER_2_Bay TOWER_4_Bay TOWER_4_Bay_J TOWER_4_Bay_S TOWER_5_Bay TOWER_6_Bay TOWER_8_Bay TOWER_12_Bay)

# 임시 디렉터리 생성
TEMP_DIR="/tmp/storagepanel_$$"
mkdir -p "${TEMP_DIR}" || { log_message "ERROR: Failed to create temp directory"; exit 1; }
trap 'rm -rf "${TEMP_DIR}"' EXIT

# 임시 파일에 명령어 작성
cat > "${TEMP_DIR}/modify_script.sh" << 'EOF'
#!/bin/bash
FILE_JS="$1"
FILE_GZ="$2"
HDD_BAY="$3"
UNIQUE="$4"
OLD="$5"
NEW="$6"

# 파일 압축 해제
gzip -dc "${FILE_GZ}" > "${FILE_JS}" || exit 1

# 설정 변경
sed -i "s/"${UNIQUE}",//g; s/,"${UNIQUE}"//g; s/${HDD_BAY}:\["/${HDD_BAY}:\["${UNIQUE}","/g; s/M2X1:\["/M2X1:\["${UNIQUE}","/g; s/${OLD}/${NEW}/g" "${FILE_JS}" || exit 1

# 파일 재압축
gzip -c "${FILE_JS}" > "${FILE_GZ}.tmp" && mv "${FILE_GZ}.tmp" "${FILE_GZ}" || exit 1
EOF

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

# 안전한 파일 수정을 위한 함수
safe_modify_file() {
    local source="$1"
    local target="$2"
    local operation="$3"
    
    # 임시 파일 생성
    local temp_file="${target}.tmp.$$"
    
    # 작업 수행
    if ! eval "$operation" > "${temp_file}"; then
        log_message "ERROR: Failed to perform operation on ${target}"
        rm -f "${temp_file}"
        return 1
    fi
    
    # 임시 파일이 비어있지 않은지 확인
    if [ ! -s "${temp_file}" ]; then
        log_message "ERROR: Operation resulted in empty file"
        rm -f "${temp_file}"
        return 1
    }
    
    # 파일 교체
    if ! mv "${temp_file}" "${target}"; then
        log_message "ERROR: Failed to replace ${target}"
        rm -f "${temp_file}"
        return 1
    fi
    
    return 0
}

# 파일 존재 여부 확인
check_file_exists() {
    local file="$1"
    if [ ! -f "$file" ]; then
        log_message "ERROR: File does not exist: $file"
        return 1
    fi
    return 0
}

# JS 파일 존재 여부 확인
log_message "Checking files: FILE_JS=${FILE_JS}, FILE_GZ=${FILE_GZ}"
log_message "Current permissions: $(ls -l ${FILE_JS})"

# 파일 권한 확인
if ! check_file_permissions "${FILE_JS}"; then
    log_message "ERROR: Cannot access ${FILE_JS}. Please ensure the package has proper permissions"
    echo "ERROR: Cannot access ${FILE_JS}. This package requires proper permissions to modify storage panel settings."
    echo "Please contact your system administrator to grant necessary permissions to the StorageManager files."
    exit 1
fi

# 파일 소유자 확인
OWNER=$(stat -c "%U:%G" "${FILE_JS}" 2>/dev/null || stat -f "%Su:%Sg" "${FILE_JS}")
log_message "File owner: ${OWNER}"

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

# Ensure backup directory exists with proper permissions
BACKUP_DIR="/var/packages/Changepanelsize/var/backups"
mkdir -p "${BACKUP_DIR}"
chmod 755 "${BACKUP_DIR}"

# Create timestamped backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/storage_panel_${TIMESTAMP}.js.gz"
if ! cp -f "${FILE_GZ}" "${BACKUP_FILE}"; then
    log_message "WARNING: Failed to create backup at ${BACKUP_FILE}"
else
    log_message "Backup created: ${BACKUP_FILE}"
fi

# Create standard backup if it doesn't exist
[ ! -f "${FILE_GZ}.bak" ] && cp -f "${FILE_GZ}" "${FILE_GZ}.bak"

# Apply configuration
log_message "Extracting gzip file..."
if ! gzip -dc "${FILE_GZ}" >"${FILE_JS}.tmp"; then
    log_message "ERROR: Failed to extract gzip file"
    exit 1
fi

# Check if temporary file was created successfully
if [ ! -f "${FILE_JS}.tmp" ]; then
    log_message "ERROR: Failed to create temporary file"
    exit 1
fi

# Replace main file
if ! mv "${FILE_JS}.tmp" "${FILE_JS}"; then
    log_message "ERROR: Failed to replace main file"
    rm -f "${FILE_JS}.tmp"
    exit 1
fi

log_message "Setting storage panel to ${HDD_BAY} ${SSD_BAY}"
log_message "Current file checksum: $(md5sum "${FILE_JS}" 2>/dev/null || md5 "${FILE_JS}")"

OLD="driveShape:\"Mdot2-shape\",major:\"row\",rowDir:\"UD\",colDir:\"LR\",driveSection:\[{top:14,left:18,rowCnt:[0-9]\+,colCnt:[0-9]\+,xGap:6,yGap:6}\]},"
NEW="driveShape:\"Mdot2-shape\",major:\"row\",rowDir:\"UD\",colDir:\"LR\",driveSection:\[{top:14,left:18,rowCnt:${SSD_BAY%%X*},colCnt:${SSD_BAY##*X},xGap:6,yGap:6}\]},"

# 파일 내용 백업
log_message "Creating backup of current content"
cp "${FILE_JS}" "${FILE_JS}.bak.$(date +%s)"

# 변경사항 확인
log_message "Verifying changes..."
if ! grep -q "${HDD_BAY}:\[\"${_UNIQUE}\"" "${FILE_JS}"; then
    log_message "ERROR: Failed to verify changes in JS file"
    echo "ERROR: Changes could not be verified"
    # 백업에서 복구
    if [ -f "${FILE_JS}.bak.$(date +%s)" ]; then
        mv "${FILE_JS}.bak.$(date +%s)" "${FILE_JS}"
        log_message "Restored from backup"
    fi
    exit 1
fi

# GZ 파일 업데이트
log_message "Updating GZ file..."
if ! safe_modify_file "${FILE_JS}" "${FILE_GZ}" "gzip -c '${FILE_JS}'"; then
    log_message "ERROR: Failed to update GZ file"
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

log_message "Storage panel configuration applied successfully: ${HDD_BAY} ${SSD_BAY}"
echo "Storage panel set to ${HDD_BAY} ${SSD_BAY}"

exit 0