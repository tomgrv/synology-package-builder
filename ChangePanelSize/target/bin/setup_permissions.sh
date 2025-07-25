#!/bin/bash

USER1="Changepanelsize"
USER2="StorageManager"
TARGETS=(
  "/usr/local/packages/@appstore/StorageManager/ui/storage_panel.js"
  "/usr/local/packages/@appstore/StorageManager/ui/storage_panel.js.gz"
)

DIR="/usr/local/packages/@appstore/StorageManager/ui"

# 중복 등록 방지를 위해 기존 ACL 확인용 함수
function has_ace() {
    local path="$1"
    local user="$2"
    synoacltool -get "$path" | grep -qE "^(user|group):${user}:"
}

echo "=== synoacltool로 ACL 권한 부여 시작 ==="

for file in "${TARGETS[@]}"; do
    if [ -f "$file" ]; then
        for user in "$USER1" "$USER2"; do
            if ! has_ace "$file" "$user"; then
                echo "[$(date)] Adding ACL for $user on $file"
                synoacltool -addace "$file" "user:$user:allow:rwxpdDaARWcCo:fd--"
            else
                echo "[$(date)] ACL for $user already exists on $file"
            fi
        done
    else
        echo "[$(date)] WARNING: 파일 없음: $file"
    fi
done

# 디렉터리에 대해서도 동일한 권한 부여 (rwX)
for user in "$USER1" "$USER2"; do
    if ! has_ace "$DIR" "$user"; then
        echo "[$(date)] Adding ACL for $user on directory $DIR"
        synoacltool -addace "$DIR" "user:$user:allow:rwxpdDaARWcCo:fdin"
    else
        echo "[$(date)] ACL for $user already exists on directory $DIR"
    fi
done

echo "=== ACL 권한 부여 완료 ==="
