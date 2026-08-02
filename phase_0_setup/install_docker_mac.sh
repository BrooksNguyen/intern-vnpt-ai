#!/bin/bash
set -e

echo "Install docker lẹ nè..."

DMG_PATH="Docker.dmg"
URL="https://desktop.docker.com/mac/main/arm64/Docker.dmg"

if [ ! -f "$DMG_PATH" ]; then
    echo "Downloading DMG (Apple Silicon)..."
    curl -L -k -o "$DMG_PATH" "$URL"
    echo "Tải xong!"
else
    echo "File DMG có sẵn rồi, skip down."
fi

echo "Mounting..."
mount_info=$(hdiutil attach "$DMG_PATH" -nobrowse)
echo "$mount_info"
mount_point=$(echo "$mount_info" | grep "/Volumes/Docker" | awk -F'\t' '{print $NF}' | xargs)

if [ -z "$mount_point" ]; then
    mount_point="/Volumes/Docker"
fi

echo "Mount tại: $mount_point"

echo "Copy vào app (chờ hơi lâu tí nha)..."
cp -R "$mount_point/Docker.app" "/Applications/"

echo "Unmount..."
hdiutil detach "$mount_point"

echo "Cleaning up..."
rm -f "$DMG_PATH"

echo "Cài xong!"
echo "Mở Docker app..."
open -a Docker

echo "Done! Check menu bar nhé."
