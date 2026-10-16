# Cách dùng Study AI V2

## Mở đúng bản

Mở `D:\pop\study_ai_v2\run_v2_visible.bat` khi cần xem tool đang đọc gì; dùng `run_v2.bat` để chạy nền. Cả hai chọn profile Deep Learning với Qwen3.5-2B + mmproj. `run_web.bat` chọn profile Web.

Nếu bản cũ ở `D:\pop\web_app_study_ai` vẫn chạy, bấm **Ctrl+1** để thoát rồi mở launcher trong folder mới. Hai folder dùng chung khóa một phiên; không chạy song song. Tách folder hoặc mở launcher mới không tự chuyển phiên đang chạy sang code/profile mới. **Ctrl+Alt+W** bật lại qua lối tắt Windows đã cài; khi cần chắc chắn chọn Deep Learning ở workspace mới, dùng `run_v2.bat` trực tiếp.

## Phím tắt hiện tại

Bảng này theo `fast_v2/ui_settings.json` của workspace mới. Nếu đổi phím trong Cài đặt, cấu hình đã lưu là căn cứ.

| Phím | Tác dụng |
| --- | --- |
| **Ctrl+Alt+Shift+P** | Mở Cài đặt. |
| **Ctrl+1** | Thoát ứng dụng. |
| **Ctrl+Q** | Đổi giữa Tự đọc cả vùng và Vẽ từng ô. |
| **Ctrl+Alt+`** | Chọn góc tại vị trí chuột; hai lần tạo một vùng. Dấu ` là backtick/grave, thường ở bên trái số 1. |
| **Ctrl+Enter** | Giải câu hỏi trong vùng đã chọn. |
| **Ctrl+Alt+R** | Bắt đầu vẽ lại bộ ô Đề và các đáp án. |
| **Backspace** | Bỏ góc hoặc ô vừa vẽ, chỉ khi đang vẽ bộ ô. |
| **Esc** | Hủy lượt vẽ bộ ô, giữ bộ cũ, chỉ khi đang vẽ. |
| **Giữ F7** | Hiện đáp án; thả để ẩn. |
| **Giữ F8** | Hiện khung vùng chụp; thả để ẩn. |
| **Ctrl+Alt+W** | Bật lại sau khi thoát, qua lối tắt Windows. |

## Tự đọc cả vùng

1. Bấm **Ctrl+Q** nếu cần để về **Tự đọc cả vùng**; có thể xem chế độ trong Cài đặt.
2. Đưa chuột tới một góc của toàn bộ câu hỏi và bấm **Ctrl+Alt+`**.
3. Di chuột tới góc đối diện rồi bấm **Ctrl+Alt+`** lần nữa. Bao đủ đề, hình/sơ đồ và các đáp án, tránh lấy cả câu bên cạnh hoặc nút điều hướng.
4. Tool theo dõi vùng và chuẩn bị OCR khi ảnh ổn định. Bấm **Ctrl+Enter** khi muốn giải.
5. Khi có đáp án, giữ **F7** để xem. Tool copy chữ đáp án vào Clipboard; bấm **Ctrl+V** ở nơi cần dán. Tool không tự chọn nút đáp án trên trang.

Vùng được lưu để dùng cho các câu sau có cùng bố cục. Giữ **F8** để xem vùng có còn đúng chỗ. Nếu trang cuộn, đổi zoom hoặc cửa sổ di chuyển, dùng phím chọn góc hai lần để chọn lại toàn vùng. **Ctrl+Alt+R** dùng để vẽ bộ ô riêng ở phần dưới.

## Vẽ riêng Đề / A / B / C / D

Dùng cách này khi đáp án chia hai cột, ô dài, hoặc tự tách bố cục không đúng.

1. Bấm **Ctrl+Q** để chọn **Vẽ từng ô**, rồi **Ctrl+Alt+R** để bắt đầu bộ mới.
2. Chọn hai góc của ô **Đề** bằng **Ctrl+Alt+`** hai lần. Bao cả hình hoặc đoạn code thuộc đề.
3. Chọn hai góc của ô **A**, rồi làm tương tự cho **B**, **C**, **D**, đúng thứ tự. Một bộ 4 đáp án cần 10 lần bấm phím chọn góc.
4. Vẽ đủ bộ thì tool tự lưu. Bấm **Ctrl+Enter** để giải; giữ **F7** để hiện đáp án hoặc dán bằng **Ctrl+V**.

Trong lúc vẽ, **Backspace** lùi một góc/ô và **Esc** hủy lượt đang vẽ. Bộ cũ chỉ được thay khi đã vẽ đủ bộ mới; phím giải không dùng bộ cũ trong khi bạn đang vẽ dở.

Bộ ô được tái sử dụng. Khi layout, màn hình, DPI hoặc số đáp án thay đổi, bấm **Ctrl+Alt+R** và vẽ lại. Số đáp án chỉnh được trong Cài đặt; mặc định hiện tại là 4, ứng dụng hỗ trợ 2–8 ô đáp án.

## Câu có ảnh, sơ đồ hoặc code

Profile Deep Learning dùng cả ảnh chụp và chữ đọc được. Hãy chọn vùng bao trọn hình, mũi tên, công thức hoặc code và các đáp án liên quan. Với bộ ô riêng, ảnh các ô được ghép theo thứ tự Đề/A/B/C/D để model đọc. Extension DOM là tùy chọn, xem `fast_v2/browser_extension/README.md`; nó không thay việc chọn vùng ảnh chính xác.

Mở bản visible để kiểm tra ảnh thực sự chụp được, chữ OCR và lỗi. OCR có thể đọc sai ký tự hoặc cấu trúc code; hỗ trợ đọc ảnh không bảo đảm đáp án luôn đúng.

## Chấm trạng thái

Bản nền có chấm nhỏ ở góc dưới phải vùng làm việc của màn hình chứa vùng chụp, cách mép taskbar 6 px logic nên không nằm sau taskbar. Màu theo `fast_v2/debug_ui.py`, lớp `StatusDot`:

| Màu | Trạng thái |
| --- | --- |
| Xám | Đang khởi tạo/nạp model. |
| Xanh dương | Chờ vùng hoặc ảnh. |
| Xanh ngọc | Đang đọc ảnh/OCR. |
| Tím | Đã chuẩn bị xong câu hỏi. |
| Cam | Đang suy luận. |
| Xanh lá | Có đáp án và đã copy. |
| Vàng | Ảnh thay đổi; cần giải lại câu hiện tại. |
| Đỏ | Có lỗi; mở bản visible để xem nguyên nhân. |

## Cài đặt và xử lý nhanh

Mở **Ctrl+Alt+Shift+P**, hoặc chạy `open_settings.bat` ở thư mục gốc nếu không dùng được phím, để đổi phím, chế độ đọc, số đáp án, độ hiện đáp án/khung hoặc tùy chọn chạy cùng Windows. Nhấp trường phím rồi bấm tổ hợp thực tế. Khi Cài đặt đang mở, hotkey toàn cục tạm dừng. Cửa sổ được đưa lên màn hình đang đặt chuột. Các tổ hợp action dùng đăng ký phím của Windows, không bị chặn chỉ vì đang giữ F7/F8; nếu tổ hợp đã bị phần mềm khác chiếm, bản visible sẽ báo lỗi đăng ký.

Nếu không có đáp án hoặc chấm đỏ: mở `run_v2_visible.bat`, kiểm tra ảnh/các ô, vẽ lại vùng rồi giải lại. Nếu chưa mở được ứng dụng, chạy `check_v2.bat` tại thư mục gốc để xem môi trường và tài nguyên. Launcher dùng `.venv` khi có, nếu không sẽ tìm Python 3.12 ở `%LOCALAPPDATA%\Programs\Python\Python312`; interpreter được chọn phải có thư viện trong `requirements.txt`.

Nếu model báo quá nóng hoặc thiếu RAM, đợi máy nguội/giải phóng bộ nhớ rồi thử lại. Không cần tải model mỗi lần chạy. Training/fine-tune là bước riêng, chưa có đủ HF weights và môi trường; không suy ra chất lượng model từ việc mở ứng dụng thành công.
