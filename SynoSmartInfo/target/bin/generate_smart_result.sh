#!/bin/bash
# /var/packages/Synosmartinfo/target/bin/generate_smart_result.sh

RESULT_DIR="/usr/syno/synoman/webman/3rdparty/Synosmartinfo/result"
RESULT_FILE="$RESULT_DIR/smart.result"
TMP_FILE="$RESULT_FILE.tmp"
SMART_SCRIPT="/var/packages/Synosmartinfo/target/bin/syno_smart_info.sh"

# Ensure result directory exists
mkdir -p "$RESULT_DIR"
chmod 755 "$RESULT_DIR"

# Run SMART info script and save output atomically
sudo "$SMART_SCRIPT" > "$TMP_FILE" 2>&1

if [ $? -eq 0 ]; then
    mv "$TMP_FILE" "$RESULT_FILE"
    chmod 644 "$RESULT_FILE"
    echo "SMART result updated successfully"
else
    echo "ERROR: Failed to run syno_smart_info.sh" > "$RESULT_FILE"
    cat "$TMP_FILE" >> "$RESULT_FILE"
    rm -f "$TMP_FILE"
    exit 1
fi
