#!/bin/bash
set -e

echo "Bắt đầu quá trình cài đặt Docker Desktop cho macOS (Apple Silicon)..."

DMG_PATH="Docker.dmg"
URL="https://desktop.docker.com/mac/main/arm64/Docker.dmg"

if [ ! -f "$DMG_PATH" ]; then
    echo "Đang tải xuống tệp cài đặt DMG từ Docker..."
    curl -L -k -o "$DMG_PATH" "$URL"
    echo "Tải xuống hoàn tất."
else
    echo "Phát hiện tệp DMG đã tồn tại trong hệ thống. Bỏ qua bước tải xuống."
fi

echo "Đang tiến hành mount tệp DMG..."
mount_info=$(hdiutil attach "$DMG_PATH" -nobrowse)
echo "$mount_info"
mount_point=$(echo "$mount_info" | grep "/Volumes/Docker" | awk -F'\t' '{print $NF}' | xargs)

if [ -z "$mount_point" ]; then
    mount_point="/Volumes/Docker"
fi

echo "Đã mount thành công tại phân vùng: $mount_point"

echo "Đang sao chép ứng dụng Docker vào thư mục /Applications (Quá trình này có thể mất vài phút)..."
cp -R "$mount_point/Docker.app" "/Applications/"

echo "Đang unmount phân vùng cài đặt..."
hdiutil detach "$mount_point"

echo "Đang dọn dẹp các tệp tin tạm..."
rm -f "$DMG_PATH"

echo "Cài đặt Docker Desktop thành công."
echo "Đang khởi động dịch vụ Docker..."
open -a Docker

echo "Tiến trình hoàn tất. Vui lòng kiểm tra trạng thái hoạt động của Docker trên thanh Menu Bar."
