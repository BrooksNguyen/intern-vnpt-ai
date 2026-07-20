# PHASE 5: XÂY DỰNG API & DASHBOARD STREAMLIT (Tuần 11 - 12)

## 📅 Tuần 11: Xây dựng API hỗ trợ phân trang (Pagination)
* **Mục tiêu:** Viết một API dịch vụ web đơn giản (dùng `FastAPI` hoặc `Flask`) để truy vấn dữ liệu từ ScyllaDB hỗ trợ tính năng phân trang khi cuộn tin nhắn.
* **Nhiệm vụ:**
  1. Sử dụng thư viện `FastAPI` để dựng các endpoint cơ bản.
  2. Kết nối tới ScyllaDB từ API bằng driver python.
  3. Viết endpoint `/messages` nhận tham số `room_id`, `limit` (số lượng tin nhắn trên 1 trang), và `state` (token phân trang của Cassandra/ScyllaDB) để trả về danh sách tin nhắn cùng token trang tiếp theo.
* **Định nghĩa hoàn thành (DoD):**
  - Chạy local server FastAPI thành công trên cổng `8000`.
  - Dùng Postman hoặc trình duyệt gọi thử `/messages?room_id=room_1&limit=10` trả về đúng định dạng JSON chứa dữ liệu tin nhắn và `paging_state` để phân trang tiếp theo.

## 📅 Tuần 12: Xây dựng Dashboard báo cáo với Streamlit
* **Mục tiêu:** Thiết kế giao diện Dashboard trực quan, tương tác thời gian thực hiển thị toàn bộ kết quả phân tích hệ thống chat cho Mentor và sếp xem.
* **Nhiệm vụ:**
  1. Sử dụng thư viện `Streamlit` để tạo nhanh giao diện web bằng Python.
  2. Tạo các widget tương tác:
     - Hộp chọn (Selectbox) để lọc dữ liệu hiển thị theo từng Room ID.
     - Biểu đồ thống kê số lượng tin nhắn và biểu đồ cảm xúc (Positive/Negative/Neutral).
     - Hiển thị hình ảnh WordCloud đã sinh ra ở Phase 4.
  3. Tích hợp đọc trực tiếp dữ liệu từ ScyllaDB để hiển thị lên Dashboard.
* **Định nghĩa hoàn thành (DoD):**
  - Khởi chạy thành công ứng dụng Streamlit cục bộ bằng lệnh:
    ```bash
    streamlit run app.py
    ```
  - Mở trình duyệt Web thấy giao diện dashboard load biểu đồ đẹp mắt, mượt mà và tương tác chọn phòng chat hoạt động đúng logic lọc dữ liệu.
