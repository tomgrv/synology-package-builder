#!/bin/sh

### Ensure correct access rights
_ws="${containerWorkspaceFolder:-.}"
sudo find "$_ws" -mindepth 1 \( -name '.git' -prune \) -o \( -exec chown vscode:vscode {} \; \)
sudo find "$_ws" -mindepth 1 \( -name '.git' -prune \) -o \( -type d -exec chmod 755 {} \; \)
sudo find "$_ws" -mindepth 1 \( -name '.git' -prune \) -o \( -type f -exec chmod 644 {} \; \)
