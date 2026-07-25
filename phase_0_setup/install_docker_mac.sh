#!/bin/bash
set -e

echo "Bắt đầu quá trình cài đặt Docker Desktop..."

DMG_PATH="Docker.dmg"
URL="https://desktop.docker.com/mac/main/arm64/Docker.dmg"

if [ ! -f "$DMG_PATH" ]; then
    echo "Đang tải Docker Desktop cho Apple Silicon (540MB)..."
    curl -L -k -o "$DMG_PATH" "$URL"
    echo "Tải về hoàn tất!"
else
    echo "Docker.dmg đã tồn tại. Bỏ qua bước tải xuống."
fi

echo "Đang mount file DMG..."
# Mount file dmg và trích xuất đường dẫn mount
mount_info=$(hdiutil attach "$DMG_PATH" -nobrowse)
echo "$mount_info"
mount_point=$(echo "$mount_info" | grep "/Volumes/Docker" | awk -F'\t' '{print $NF}' | xargs)

if [ -z "$mount_point" ]; then
    mount_point="/Volumes/Docker"
fi

echo "Đã mount tại: $mount_point"

echo "Đang sao chép Docker.app vào /Applications (quá trình này có thể mất vài phút)..."
# Sao chép ứng dụng vào thư mục /Applications.
cp -R "$mount_point/Docker.app" "/Applications/"

echo "Đang unmount DMG..."
hdiutil detach "$mount_point"

echo "Đang dọn dẹp file cài đặt..."
rm -f "$DMG_PATH"

echo "Đã cài đặt thành công Docker Desktop trong /Applications!"
echo "Đang mở Docker Desktop để khởi tạo dịch vụ..."
open -a Docker

echo "Script hỗ trợ cài đặt hoàn thành! Vui lòng kiểm tra Docker Desktop trên thanh menu của bạn."
