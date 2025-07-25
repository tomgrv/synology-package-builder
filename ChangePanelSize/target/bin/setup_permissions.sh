#!/bin/bash

USER1="Changepanelsize"
USER2="StorageManager"
TARGETS=(
  "/usr/local/packages/@appstore/StorageManager/ui/storage_panel.js"
  "/usr/local/packages/@appstore/StorageManager/ui/storage_panel.js.gz"
)

# 1. 사용자별 ACL 권한 부여 (읽기/쓰기)
for file in "${TARGETS[@]}"; do
    if [ -f "$file" ]; then
        setfacl -m u:$USER1:rw "$file"
        setfacl -m u:$USER2:rw "$file"
    fi
done

# 2. 디렉터리에도 필요한 경우 동일하게 적용
DIR="/usr/local/packages/@appstore/StorageManager/ui"
setfacl -m u:$USER1:rwX "$DIR"
setfacl -m u:$USER2:rwX "$DIR"
