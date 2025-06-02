#!/bin/sh

### Ensure correct access rights
sudo chown -Rf vscode:vscode ${containerWorkspaceFolder:-.}/* ${containerWorkspaceFolder:-.}/.*
sudo chmod -Rf 755 ${containerWorkspaceFolder:-.}/* ${containerWorkspaceFolder:-.}/.*
