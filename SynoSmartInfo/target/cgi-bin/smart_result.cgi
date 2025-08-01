#!/bin/bash
# /var/packages/Synosmartinfo/target/cgi-bin/smart_result.cgi
# This CGI script runs the syno_smart_info.sh script and saves output to result file, then outputs content

RESULT_DIR="/var/services/web/Synosmartinfo/result"
RESULT_FILE="$RESULT_DIR/smart.result"
TMP_FILE="$RESULT_FILE.tmp"

SMART_SCRIPT="/var/packages/Synosmartinfo/target/bin/syno_smart_info.sh"

echo "Content-Type: text/plain; charset=utf-8"
echo ""

# Ensure result directory exists
mkdir -p "$RESULT_DIR"
chmod 755 "$RESULT_DIR"

# Run SMART info script and save output atomically
"$SMART_SCRIPT" > "$TMP_FILE" 2>&1

if [ $? -eq 0 ]; then
    mv "$TMP_FILE" "$RESULT_FILE"
    chmod 644 "$RESULT_FILE"
else
    echo "ERROR: Failed to run syno_smart_info.sh"
    cat "$TMP_FILE"
    rm -f "$TMP_FILE"
    exit 1
fi

# Output the result file content to the web client
cat "$RESULT_FILE"
