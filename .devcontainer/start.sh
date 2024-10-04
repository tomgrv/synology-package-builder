#!/bin/sh

### Make sure the workspace folder is owned by the user
git config --global --add safe.directory ${containerWorkspaceFolder:-.}

### Self update
echo "Self updating devcontainer..."
npx --yes $(sed -e 's://.*$::g' .devcontainer/devcontainer.json | npx --yes jqn '.name' | tr -d "'[]:,")  -a
