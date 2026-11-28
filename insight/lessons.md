# Bài học cho video tiếp theo (cập nhật 19:39 28/11/2026)

## Bot review (5 video gần nhất từ bản chuẩn)
Điểm trung bình: Hình ảnh rõ ràng 5.4, Video ngắn 6.0, Dữ liệu đúng ý 6.7, dang_xem 6.8, Ảnh bìa 6.9, Nhịp độ 7.1, Hook 3 giây đầu 7.5, Phụ đề 7.8, Màu sắc thương hiệu 8.7
Yếu nhất (ưu tiên sửa): Hình ảnh rõ ràng, Video ngắn, Dữ liệu đúng ý

### Mẹo viết lời đọc
- Hook nên đi thẳng vào nỗi đau: 'Tại sao bạn luôn mua đúng đỉnh?' thay vì kể chuyện năm 1929 trước. Đưa kết quả Bitcoin lên đầu.
- Đoạn giữa (giây 80-100) quá giống sách giáo khoa. Hãy dùng câu hỏi: 'Ông già từ thế kỷ 19 thì giúp gì được cho túi tiền crypto của bạn?' để kéo người xem lại.
- Kết thúc cần một Call-to-action mạnh hơn: 'Mở chart BTC ra, đếm ngay đỉnh đáy và comment xem chúng ta đang ở giai đoạn nào'.
- Hook rất tốt nhưng đoạn giữa (giây 82-100) hơi bị trùng xuống do kể lể lịch sử. Nên lồng thêm câu: 'Tại sao một lý thuyết từ thời xe ngựa lại đúng với Bitcoin?' để giữ chân.
- Sử dụng nhiều hơn các từ chỉ hành động mạnh: 'thủng đáy', 'quét sạch', 'lặng lẽ rút lui' thay vì chỉ 'giá giảm', 'người bán'.
- Hook: Thay vì hỏi 'Rat race là gì', hãy bắt đầu bằng một con số gây sốc hơn như 'Bạn đang làm không công 15 ngày mỗi tháng cho ngân hàng mà không biết'.
- Độ dài: Đoạn giải thích định nghĩa (long_6 đến long_10) hơi dài dòng, có thể gộp các ý định nghĩa vào thẳng ví dụ thực tế để rút ngắn 30s, đẩy nhanh đến phần '3 lối thoát'.
- Hook: Thay vì hỏi 'Bí quyết đó là gì?', hãy dùng '3 bước để Hamilton nhìn ra cú sập mà cả thế giới ngó lơ'. Cụ thể hóa bí quyết ngay từ đầu.

### Đoạn dễ mất người xem
- [20261128-1916] Đoạn từ giây 82 đến 110 (giới thiệu Charles Dow) dễ làm người xem thoát vì cảm giác đang học lịch sử chứ không phải tìm kèo đầu tư.
- [20261128-1553] Đoạn từ giây 90 đến 105 dễ mất người xem vì giảng giải định nghĩa 3 loại xu hướng quá giống sách giáo khoa, thiếu ví dụ thực tế ngay lập tức.
- [20261128-0030] Đoạn từ giây 107 đến 143 (long_6 đến long_8) dễ mất người xem vì nặng tính lý thuyết định nghĩa và hình ảnh minh họa bắt đầu bị lặp lại, thiếu các con số nhảy liên tục như đoạn đầu.

### Việc cần sửa ở video gần nhất (phiên Claude sửa code nếu là lỗi hình ảnh)
- [20261128-1916] long_0: Chữ 'Mua đúng đỉnh...' trong thẻ quá nhỏ so với khoảng trắng. Sửa: Phóng to chữ chiếm 70% diện tích thẻ để tạo cú đập thị giác ngay giây đầu.
- [20261128-1916] long_4: KHÔNG ĐÁNG: Thẻ chỉ ghi 'Vì vậy mới có phân tích kỹ thuật' lặp lại y hệt lời đọc mà không có hình minh hoạ. Sửa: Thay bằng icon biểu đồ nến bị một đống báo chí đè lên.
- [20261128-1916] long_11: Con số '12' quá đơn điệu. Sửa: Hiệu ứng số đếm chạy từ 1 đến 12, kèm logo các công ty thời đó (GE, US Steel) để tăng tính lịch sử.
- [20261128-1916] long_18: Biểu đồ BTC quá nhỏ và mờ. Sửa: Crop sát vào đoạn giá đang chạy, dùng hiệu ứng vẽ đường line (Path property) chạy theo lời đọc.
- [20261128-1916] long_31: LỖI TRÌNH BÀY: '12%/năm' dùng dấu gạch chéo dễ bị máy ngắt dòng sai. Sửa: Viết '12% mỗi năm' hoặc để '12%' to, 'mỗi năm' nhỏ ở dưới.
- [20261128-1916] long_32: KHÔNG ĐÁNG: Thẻ trống trơn chỉ có dấu ngoặc kép. Sửa: Thêm text 'Kế hoạch > Dự báo' hoặc hình ảnh một người cắt lỗ (Stop loss) để minh hoạ ý 'biết mình sai'.
- [20261128-1916] long_35: LỖI TRÌNH BÀY: Các dòng tóm tắt xuất hiện cùng lúc làm người xem lười đọc. Sửa: Cho từng dòng hiện ra kèm tiếng 'pop' theo nhịp liệt kê.
- [20261128-1916] short0_0: Tỷ lệ 9:16 nhưng thẻ thông tin vẫn giữ nguyên layout ngang của bản 16:9. Sửa: Thiết kế lại thẻ dọc, đẩy chữ lên cao để không bị thanh công cụ TikTok che.
- [20261128-1916] NGƯỜI XEM: long_10 đến long_13: Đoạn tiểu sử Charles Dow quá dài và khô. Sửa: Cắt bớt 5s, lồng ghép hình ảnh tờ báo Wall Street Journal cũ để tăng tính kể chuyện.
- [20261128-1916] NGƯỜI XEM: long_22: 'Tích luỹ', 'Tham gia', 'Phân phối' chỉ là chữ. Sửa: Vẽ một đường giá hình sin đi qua 3 giai đoạn này, highlight vùng đang nói.
- [20261128-1916] LỖI SOÁT: long_21 thẻ bên phải ghi 'Thủy triều đổi chiều' nhưng lời đọc là 'đếm đỉnh và đáy'. Sửa: Text trên hình phải là 'Đỉnh thấp hơn + Đáy thấp hơn = Đảo chiều'.
