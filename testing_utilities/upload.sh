#!/bin/bash

# Variables - update these with your settings
SOURCE_FOLDER="/Users/isaac/Developer/Projects/litebox/litebox"
DEST_USER="pi"
DEST_HOST="192.168.8.103"
DEST_FOLDER="/home/pi"
SSH_PASSWORD="raspberry"  # Hardcoded password (insecure)

echo "Copying folder from '$SOURCE_FOLDER' to '$DEST_USER@$DEST_HOST:$DEST_FOLDER'..."

# Use sshpass to pass the password non-interactively
sshpass -p "$SSH_PASSWORD" scp -r "$SOURCE_FOLDER" "$DEST_USER@$DEST_HOST:$DEST_FOLDER"

if [ $? -eq 0 ]; then
    echo "Folder copied successfully."
else
    echo "Error: Folder copying failed."
fi
