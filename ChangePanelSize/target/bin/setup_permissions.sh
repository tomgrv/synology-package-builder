#!/bin/bash

USER1="Changepanelsize"
USER2="StorageManager"
TARGETS=(
  "/usr/local/packages/@appstore/StorageManager/ui/storage_panel.js"
  "/usr/local/packages/@appstore/StorageManager/ui/storage_panel.js.gz"
)
DIR="/usr/local/packages/@appstore/StorageManager/ui"

# synoacltool을 통한 ACL 수정 함수
set_acl() {
  local user=$1
  local path=$2
  # 읽기 쓰기 권한 부여 (r: 읽기, w: 쓰기, x: 실행 권한은 디렉토리에만 부여)
  synoacltool -add ACE:user:$user:allow:rwa:fd:allow /bin/true "$path"
}

# 1. 파일에 대해 사용자별 ACL 권한 부여 (읽기/쓰기)
for file in "${TARGETS[@]}"; do
  if [ -f "$file" ]; then
    set_acl "$USER1" "$file"
    set_acl "$USER2" "$file"
  fi
done

# 2. 디렉터리에 권한 부여 (실행 권한 포함)
if [ -d "$DIR" ]; then
  # 디렉터리는 실행 권한도 필요하므로 rwa+x 권한 설정
  synoacltool -add ACE:user:$USER1:allow:rwa:fd:allow /bin/true "$DIR"
  synoacltool -add ACE:user:$USER2:allow:rwa:fd:allow /bin/true "$DIR"
fi
