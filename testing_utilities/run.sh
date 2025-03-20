#!/bin/bash

# Variables - update these with your settings
DEST_USER="pi"
DEST_HOST="192.168.8.103"
SSH_PASSWORD="raspberry"  # Hardcoded password (insecure)

# Command to run on the Raspberry Pi
REMOTE_COMMAND="python3 litebox/main.py"

echo "Logging into $DEST_USER@$DEST_HOST and executing: $REMOTE_COMMAND"

# Use sshpass to pass the password non-interactively and run the command on the remote host.
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no "$DEST_USER@$DEST_HOST" "$REMOTE_COMMAND"

if [ $? -eq 0 ]; then
    echo "Remote command executed successfully."
else
    echo "Error: Remote command execution failed."
fi