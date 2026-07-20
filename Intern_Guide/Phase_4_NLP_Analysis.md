# PHASE 4: PHÂN TÍCH NLP TRÊN TIN NHẮN CHAT (Tuần 8 - 10)

## 📅 Tuần 8: Tiền xử lý văn bản (Text Preprocessing)
* **Mục tiêu:** Làm sạch dữ liệu tin nhắn chat (loại bỏ ký tự đặc biệt, link, stop words) trước khi đưa vào mô hình phân tích.
* **Nhiệm vụ:**
  1. Sử dụng thư viện `NLTK` hoặc `SpaCy` trong Python để thực hiện:
     - Chuyển văn bản tin nhắn về dạng chữ thường (lowercase).
     - Loại bỏ các dấu câu, ký tự đặc biệt và các liên kết web (URL).
     - Tokenize (tách từ) tin nhắn chat.
     - Loại bỏ các từ dừng (Stop words - những từ xuất hiện nhiều nhưng không mang giá trị ngữ nghĩa, ví dụ: "thì", "mà", "là").
  2. Viết hàm xử lý sạch dữ liệu này và chạy thử trên một tập mẫu tin nhắn chat lấy từ ScyllaDB.
* **Định nghĩa hoàn thành (DoD):**
  - Hàm làm sạch text hoạt động đúng, loại bỏ được stopwords tiếng Việt/tiếng Anh.
  - In ra màn hình kết quả so sánh trước và sau khi tiền xử lý của 5 tin nhắn mẫu.

## 📅 Tuần 9: Phân tích cảm xúc tin nhắn (Sentiment Analysis)
* **Mục tiêu:** Gán nhãn cảm xúc (Tích cực, Tiêu cực, Trung lập) cho từng tin nhắn chat của người dùng.
* **Nhiệm vụ:**
  1. Sử dụng một thư viện phân tích cảm xúc đơn giản như `VADER` (cho tiếng Anh) hoặc dùng mô hình PhoBERT/mô hình dựa trên từ điển đơn giản (cho tiếng Việt).
  2. Tính toán điểm số cảm xúc (sentiment score) cho từng dòng tin nhắn.
  3. Gán nhãn cho tin nhắn dựa trên điểm số:
     - Điểm > 0.05: Tích cực (Positive)
     - Điểm < -0.05: Tiêu cực (Negative)
     - Còn lại: Trung lập (Neutral)
* **Định nghĩa hoàn thành (DoD):**
  - Tạo thêm được cột `sentiment` trong DataFrame chứa nhãn cảm xúc tương ứng của tin nhắn.
  - Đếm và hiển thị tỉ lệ phần trăm các loại cảm xúc của toàn bộ hệ thống chat.

## 📅 Tuần 10: Thống kê giờ hoạt động cao điểm & Vẽ WordCloud
* **Mục tiêu:** Trực quan hóa dữ liệu thống kê từ kết quả phân tích NLP và giờ gửi tin nhắn.
* **Nhiệm vụ:**
  1. Thống kê số lượng tin nhắn theo từng khung giờ trong ngày (0h - 23h) để tìm ra khoảng thời gian người dùng chat nhiều nhất (Giờ cao điểm).
  2. Sử dụng thư viện `wordcloud` trong Python để vẽ đám mây từ (WordCloud) hiển thị các từ khóa xuất hiện nhiều nhất trong các tin nhắn Tích cực và Tiêu cực.
* **Định nghĩa hoàn thành (DoD):**
  - Vẽ và lưu thành công biểu đồ đường (Line chart) thể hiện lượng tin nhắn theo giờ hoạt động.
  - Xuất ra tệp hình ảnh WordCloud thể hiện các từ phổ biến nhất trong hệ thống chat.
