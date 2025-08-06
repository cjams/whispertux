#!/bin/bash

# Wrapper script for ydotoold to set proper permissions
# Remove existing socket
rm -f /tmp/.ydotool_socket

# Start ydotoold in background
/usr/bin/ydotoold &
YDOTOOLD_PID=$!

# Wait for socket to be created and fix permissions
for i in {1..30}; do
    if [ -S /tmp/.ydotool_socket ]; then
        chmod 660 /tmp/.ydotool_socket
        chgrp input /tmp/.ydotool_socket
        echo "ydotoold: socket permissions fixed (660, group: input)"
        break
    fi
    sleep 0.1
done

# Wait for ydotoold process to finish
wait $YDOTOOLD_PID
