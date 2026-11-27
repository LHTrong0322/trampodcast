# Kịch bản v4 (làm lại từ đầu, chờ Trọng duyệt): Lý thuyết Dow: chuyện ra đời, trend is your friend và backtest thật trên BTC

Video dài khoảng 6 phút. Trọng tâm: dạy lý thuyết Dow bằng chuyện ra đời, chart và backtest thật. Các ô {DOW:...} là số backtest BTC máy tự tính lúc dựng (cùng thuật toán dow() của bot radar), khớp với chart.

## Hook
Một ý tưởng từ năm 1896. Gắn vào bot trade của mình: lãi tăng 27%, sụt vốn giảm 24%.

## Mở đầu
Ý tưởng đó là lý thuyết Dow, gói gọn trong một câu: trend is your friend, đi theo xu hướng chính. Video này có chuyện ra đời, cách đọc trên chart, và 2 backtest thật: trên BTC và trên bot của mình. Chào mừng mọi người quay lại Smart Penguin Insights.

## Phần 1: Chuyện ra đời: Charles Dow và tờ Wall Street Journal
Câu chuyện bắt đầu ở New York cuối thế kỷ 19. Charles Dow là một nhà báo tài chính. Năm 1882, ông cùng Edward Jones lập ra công ty Dow Jones. Năm 1889, họ ra tờ Wall Street Journal. Thời đó, nhà đầu tư chỉ nhìn giá từng cổ phiếu riêng lẻ, nhiều mã còn bị làm giá. Dow nghĩ khác. Năm 1896, ông lấy giá 12 cổ phiếu công nghiệp lớn, cộng lại rồi chia trung bình. Đó là chỉ số Dow Jones công nghiệp. Ông theo dõi thêm một chỉ số đường sắt. Từ hai con số đó, Dow nhận ra thị trường có một xu hướng chung, giống như thuỷ triều. Ông viết khoảng 255 bài xã luận về ý tưởng này, rồi mất năm 1902. Điều thú vị: chính Dow chưa bao giờ gọi nó là lý thuyết. William Hamilton, tổng biên tập kế nhiệm, viết tiếp và ra sách năm 1922. Năm 1932, Robert Rhea hệ thống lại thành cuốn The Dow Theory. Cái tên lý thuyết Dow ra đời từ đó.
Chữ trên hình: 1882: lập Dow Jones & Company / 1889: ra tờ Wall Street Journal / 1896: chỉ số 12 cổ phiếu

## Phần 2: Case study 1929: A Turn in the Tide
Bài kiểm tra nổi tiếng nhất của lý thuyết Dow đến năm 1929. Ngày 25 tháng 10 năm 1929, Hamilton đăng bài xã luận A Turn in the Tide, tức thuỷ triều đã đổi chiều. Ông viết: theo lý thuyết Dow, tín hiệu thị trường giá xuống đã xuất hiện từ hai ngày trước. Lúc đó nhiều người vẫn cho rằng chỉ là một nhịp điều chỉnh. Kết quả: chỉ số Dow Jones từ đỉnh 381 điểm tháng 9 năm 1929 rơi về 41 điểm tháng 7 năm 1932, mất 89%. Nhưng phải công bằng. Năm 1934, nhà nghiên cứu Alfred Cowles chấm lại các bài của Hamilton từ 1902 tới 1929: theo Dow lãi khoảng 12% mỗi năm, mua rồi giữ lãi 15.5%. Năm 1998, các nhà nghiên cứu ở Yale và NYU chấm lại, tính cả rủi ro, thì Dow vẫn có lợi thế. Vậy thì sao? Dow không phải cỗ máy in tiền. Nó là chiếc phao giúp bạn né những cú sập lớn nhất.
Chữ trên hình: 25/10/1929: Hamilton báo thị trường giá xuống / Chỉ số Dow Jones: 381 về 41 / Dow giỏi né thảm hoạ, không luôn lãi nhiều hơn

## Phần 3: Dow giúp gì: trend is your friend
Vậy lý thuyết Dow giúp gì cho bạn? Nó trả lời đúng một câu hỏi quan trọng nhất: xu hướng chính lúc này là gì. Dow chia thị trường làm 3 lớp. Xu hướng chính là thuỷ triều, kéo dài từ một năm trở lên. Xu hướng phụ là con sóng, đánh ngược vài tuần đến vài tháng. Xu hướng nhỏ là gợn nước, vài ngày, gần như nhiễu. Giới trader có câu: trend is your friend, xu hướng là bạn. Đi cùng thuỷ triều, bạn được cả thị trường đẩy đi. Đi ngược, bạn phải đúng liên tục mới sống được. Biết thuỷ triều đang lên, bạn không bán non khi gặp một con sóng điều chỉnh. Biết thuỷ triều đang rút, bạn không bắt dao rơi chỉ vì giá trông đã rẻ. Vế sau của câu nói mới quan trọng: until the end, cho tới khi xu hướng kết thúc. Dow cho bạn cách nhận ra lúc kết thúc đó.
CHART: BTC khung tuần: thuỷ triều lên và rút (wma)
Chữ trên hình: Biết xu hướng chính đang là gì / Không bắt dao rơi, không bán non / Đứng ngoài khi downtrend

## Phần 4: Đọc Dow trên chart: đỉnh và đáy
Nhận ra bằng cách nào? Nhìn đỉnh và đáy. Uptrend là chuỗi HH và HL: higher high, đỉnh sau cao hơn đỉnh trước, higher low, đáy sau cao hơn đáy trước. Downtrend là chuỗi LH và LL, ngược lại. Đây là BTC khung tuần, đỉnh đáy do máy tự đánh dấu bằng đúng thuật toán trong bot của mình. Màu xanh là HH và HL, màu đỏ là LH và LL. Nhìn giai đoạn 2023 tới 2025: chuỗi xanh nối tiếp, đỉnh và đáy cứ cao dần lên tới $126K. Rồi năm 2026: nhịp hồi lớn nhất chỉ lên $87.4K, một đỉnh thấp hơn. Tháng 11, giá thủng đáy $57.7K, một đáy thấp hơn. Theo Dow, xu hướng tăng đã kết thúc. Quy tắc rất đơn giản: xu hướng vẫn còn cho tới khi có tín hiệu đảo chiều rõ ràng, tức đỉnh thấp hơn rồi thủng đáy cũ. Không đoán, chỉ xác nhận.
CHART: BTC khung tuần: đỉnh và đáy theo Dow (dow, swings)
Chữ trên hình: HH + HL = xu hướng tăng / LH + LL = xu hướng giảm / Đỉnh thấp hơn + thủng đáy = đảo chiều

## Phần 5: Backtest 1: cầm BTC chỉ khi Dow báo tăng
Nghe hay, nhưng có thật hiệu quả không? Mình backtest trên giá BTC tuần thật từ đầu năm 2018. Luật chỉ có một dòng: khi cấu trúc là HH và HL thì cầm BTC, khi mất cấu trúc đó thì bán, ngồi tiền mặt. Không phí, không đòn bẩy. Kết quả: mua rồi giữ từ 2018 lãi {DOW:2018:bh}%, nhưng có lúc tài khoản sụt {DOW:2018:bhdd}% từ đỉnh. Cầm theo Dow lãi {DOW:2018:ret}%, mức sụt tối đa chỉ {DOW:2018:dd}%. Cả 8 năm, Dow chỉ cầm BTC khoảng {DOW:2018:inmkt}% thời gian, với {DOW:2018:trades} lần mua. Phần nền xanh trên chart là lúc cầm. Bạn thấy nó đứng ngoài gần hết năm 2022, đúng lúc BTC mất hơn 70%. Vậy thì sao? Cái Dow cho bạn không phải là mua đúng đáy. Nó cho bạn đứng ngoài những năm tệ nhất, để còn vốn khi thuỷ triều quay lại.
CHART: Cầm BTC khi Dow tăng, từ 2018 (dow, backtest)
Chữ trên hình: Luật: HH + HL thì cầm, mất thì ra / So với mua rồi giữ từ 2018 / Sụt vốn nhỏ hơn rất nhiều

## Phần 6: Backtest 2: gắn bộ lọc Dow vào bot của mình
Case study thứ hai là bot trade của chính mình. Bot quét 108 mã crypto, backtest gần 4 năm. Đơn vị là R, tức mỗi lệnh mình chấp nhận rủi ro đúng 1 phần cố định. Bản gốc chỉ vào lệnh khi BTC nằm trên đường EMA200 khung ngày: 407 lệnh, lãi 69.6R, sụt vốn tối đa 13.1R. Rồi mình thêm đúng một điều kiện: BTC khung ngày phải có cấu trúc Dow tăng, HH và HL. Kết quả: số lệnh giảm còn 239, nhưng lãi tăng lên 88.2R, tức thêm 27%. Sụt vốn tối đa giảm còn 9.9R. Tỷ lệ thắng từ 32.4% lên 36.8%. Ở nửa sau của giai đoạn, lúc thị trường khó, bản gốc chỉ lãi 5.8R, bản có Dow lãi 11R, gần gấp đôi. Một chi tiết quan trọng: nếu bỏ EMA200, chỉ dùng mỗi Dow, nửa sau lại lỗ 1.8R. Vậy thì sao? Dow mạnh nhất khi làm bộ lọc, kết hợp với công cụ khác, không phải đứng một mình.
Chữ trên hình: Bot chỉ dùng EMA200: 69.6R, sụt 13.1R / Thêm Dow khung ngày: 88.2R, sụt 9.9R / Ít lệnh hơn, lãi hơn, an toàn hơn

## Phần 7: Hạn chế và cách dùng Dow đúng
Dow có hạn chế không? Có, và bạn phải biết. Thứ nhất, tín hiệu luôn đến muộn. Phải chờ đỉnh đáy hình thành rồi mới xác nhận, nên Dow bỏ lỡ phần đầu và phần cuối mỗi con sóng. Thứ hai, khi thị trường đi ngang, đỉnh đáy lẫn lộn, Dow dễ báo vào ra liên tục. Cách dùng mà mình thấy hiệu quả có 3 bước. Một: mở khung tuần hoặc khung ngày, xác định cấu trúc HH HL hay LH LL. Hai: chỉ tìm lệnh mua khi cấu trúc tăng, đứng ngoài hoặc giảm vị thế khi cấu trúc gãy. Ba: kết hợp thêm một công cụ khác, như EMA200, để lọc bớt tín hiệu nhiễu. Hãy dùng lý thuyết Dow như la bàn, không phải quả cầu pha lê.
Chữ trên hình: Tín hiệu luôn đến muộn / Thị trường đi ngang: dễ báo sai / Dùng làm bộ lọc xu hướng

## Tóm lại
Tóm lại: Dow dạy bạn nhìn thuỷ triều, đi cùng xu hướng chính, và chỉ đổi ý khi đỉnh đáy xác nhận. Đây là nội dung giáo dục, không phải lời khuyên đầu tư. Bình luận cho mình biết: trước khi vào lệnh, bạn có lọc xu hướng không?

## 2 Short
- 1929: một bài báo né cú sập 89%
- Thêm 1 bộ lọc Dow: bot lãi thêm 27%

## Ảnh bìa
Số lớn +27%, chữ "trend is your friend", nhãn "lý thuyết Dow", dòng nhỏ "Chuyện ra đời + backtest thật", logo BTC.
