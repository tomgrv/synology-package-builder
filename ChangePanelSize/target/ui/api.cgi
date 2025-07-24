#!/bin/bash
# API endpoint for Storage Panel Manager

echo "Content-Type: application/json"
echo "Access-Control-Allow-Origin: *"
echo "Access-Control-Allow-Methods: GET, POST"
echo "Access-Control-Allow-Headers: Content-Type"
echo ""

# Function to return JSON response
json_response() {
    local success="$1"
    local message="$2"
    local data="$3"
    
    echo "{"
    echo "  \"success\": $success,"
    echo "  \"message\": \"$message\""
    if [ -n "$data" ]; then
        echo "  ,$data"
    fi
    echo "}"
}

# Parse request
if [ "$REQUEST_METHOD" = "POST" ]; then
    read -t 30 POST_DATA
    eval $(echo "$POST_DATA" | tr '&' ';')
elif [ "$REQUEST_METHOD" = "GET" ]; then
    eval $(echo "$QUERY_STRING" | tr '&' ';')
fi

# Get system information
_UNIQUE="$(/bin/get_key_value /etc.defaults/synoinfo.conf unique 2>/dev/null)"
_BUILD="$(/bin/get_key_value /etc.defaults/VERSION buildnumber 2>/dev/null)"

case "$action" in
    "info")
        # Return system information
        json_response "true" "System information retrieved" "\"unique\": \"${_UNIQUE}\", \"build\": \"${_BUILD}\""
        ;;
        
    "apply")
        if [ -z "$hdd_bay" ] || [ -z "$ssd_bay" ]; then
            json_response "false" "Missing required parameters: hdd_bay and ssd_bay"
            exit 0
        fi
        
        # Execute storage panel script
        RESULT=$(/var/packages/StoragePanelManager/target/bin/storagepanel.sh "$hdd_bay" "$ssd_bay" 2>&1)
        EXIT_CODE=$?
        
        if [ $EXIT_CODE -eq 0 ]; then
            json_response "true" "Configuration applied successfully: $hdd_bay $ssd_bay"
        else
            json_response "false" "Failed to apply configuration: $RESULT"
        fi
        ;;
        
    "restore")
        # Execute restore
        RESULT=$(/var/packages/StoragePanelManager/target/bin/storagepanel.sh -r 2>&1)
        EXIT_CODE=$?
        
        if [ $EXIT_CODE -eq 0 ]; then
            json_response "true" "Original configuration restored successfully"
        else
            json_response "false" "Failed to restore configuration: $RESULT"
        fi
        ;;
        
    *)
        json_response "false" "Invalid action specified"
        ;;
esac