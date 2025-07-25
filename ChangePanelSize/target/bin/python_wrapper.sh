#!/bin/bash
# Python 파일 래퍼 - 실제로는 shell script를 실행
exec /var/packages/Changepanelsize/target/bin/change_panel_size.sh "$@"
