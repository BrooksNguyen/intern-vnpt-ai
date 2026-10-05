#!/bin/bash
set -e

echo "Starting Docker Desktop installation for macOS (Apple Silicon)..."

DMG_PATH="Docker.dmg"
URL="https://desktop.docker.com/mac/main/arm64/Docker.dmg"

if [ ! -f "$DMG_PATH" ]; then
    echo "Downloading Docker DMG installer..."
    curl -L -k -o "$DMG_PATH" "$URL"
    echo "Download complete."
else
    echo "Existing DMG file detected. Skipping download."
fi

echo "Mounting DMG file..."
mount_info=$(hdiutil attach "$DMG_PATH" -nobrowse)
echo "$mount_info"
mount_point=$(echo "$mount_info" | grep "/Volumes/Docker" | awk -F'\t' '{print $NF}' | xargs)

if [ -z "$mount_point" ]; then
    mount_point="/Volumes/Docker"
fi

echo "Successfully mounted at: $mount_point"

echo "Checking for running Docker instances to prevent 'File in use' errors..."
if pgrep -xq "Docker"; then
    echo "Docker is currently running. Shutting down..."
    killall Docker || true
    sleep 3
fi

echo "Copying Docker.app to /Applications (this may take a few minutes)..."
cp -R "$mount_point/Docker.app" "/Applications/"

echo "Unmounting installer volume..."
hdiutil detach "$mount_point"

echo "Cleaning up temporary files..."
rm -f "$DMG_PATH"

echo "Docker Desktop installed successfully."
echo "Launching Docker..."
open -a Docker

echo "Installation complete. Please check the Docker status in the Menu Bar."
