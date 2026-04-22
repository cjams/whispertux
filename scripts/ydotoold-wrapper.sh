#!/bin/bash

# Wrapper script for ydotoold to set socket permissions usable by WhisperTux.
set -euo pipefail

SOCKET_PATH="${YDOTOOL_SOCKET:-/tmp/.ydotool_socket}"
SOCKET_GROUP="${YDOTOOLD_SOCKET_GROUP:-input}"

if ! SOCKET_GID="$(getent group "$SOCKET_GROUP" | cut -d: -f3)"; then
    echo "ydotoold: group '$SOCKET_GROUP' does not exist" >&2
    exit 1
fi

if [ -z "$SOCKET_GID" ]; then
    echo "ydotoold: could not resolve gid for group '$SOCKET_GROUP'" >&2
    exit 1
fi

rm -f "$SOCKET_PATH"

# Set ownership at socket creation time so clients never see a root-only socket.
exec /usr/bin/ydotoold \
    --socket-path="$SOCKET_PATH" \
    --socket-perm=0660 \
    --socket-own="0:$SOCKET_GID"
