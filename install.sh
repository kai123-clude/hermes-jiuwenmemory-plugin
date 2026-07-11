#!/usr/bin/env bash
set -euo pipefail
PLUGIN_NAME="jiuwenmemory"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="$HERMES_HOME/plugins/$PLUGIN_NAME"
mkdir -p "$(dirname "$TARGET_DIR")"
if [ -e "$TARGET_DIR" ] && [ ! -L "$TARGET_DIR" ]; then
  backup="$TARGET_DIR.backup.$(date +%Y%m%d-%H%M%S)"
  mv "$TARGET_DIR" "$backup"
  echo "Backed up existing $TARGET_DIR to $backup"
fi
ln -sfn "$SRC_DIR" "$TARGET_DIR"
echo "Installed $PLUGIN_NAME plugin link: $TARGET_DIR -> $SRC_DIR"
echo "Set memory.provider: jiuwenmemory in ~/.hermes/config.yaml and restart Hermes to activate."
