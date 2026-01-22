#!/bin/sh
# Copyright (c) 2000-2015 Synology Inc. All rights reserved.

# Ensure the context is set
if [ ! -f "$PRESETS_FILE" ]; then
    echo "Presets file not found: $PRESETS_FILE"
    exit 1
fi

# loop through all .presets.docker objects in ressource file
# for each array objecy, give profile and image fields
jq -r '.resource[]' "$PRESETS_FILE" | while read -r resource; do
    echo "Processing $SYNOPKG_PKGCONF/$resource"
    $(dirname $0)/_substitute "$SYNOPKG_CONF/$resource" "$SYNOPKG_PKGDEST/$resource" "resource"
done


exit 0
