#!/bin/sh
# Copyright (c) 2000-2015 Synology Inc. All rights reserved.

# Ensure the context is set
if [ ! -f "$PRESETS_FILE" ]; then
    echo "Presets file not found: $PRESETS_FILE"
    exit 1
fi

ll $SYNOPKG_TEMP_SPKFILE > /tmp/spkfile.list 

# loop through all .presets.docker objects in ressource file
# for each array objecy, give profile and image fields
jq -r '.resource[]' "$PRESETS_FILE" | while read -r resource; do
    echo "Processing $SYNOPKG_TEMP_SPKFILE/conf/$resource"
    $(dirname $0)/_substitute "$SYNOPKG_TEMP_SPKFILE/conf/$resource" "$SYNOPKG_TEMP_SPKFILE/conf/$resource" "resource"
done


exit 0
