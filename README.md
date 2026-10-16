# Study AI V2

`D:\pop\study_ai_v2` là workspace phát triển chính từ nay. Bản ở `D:\pop\web_app_study_ai` được giữ làm snapshot để đối chiếu và quay lại khi cần. Mã ứng dụng vẫn nằm trong `fast_v2/`.

V2 mặc định dùng profile **Deep Learning**, model **Qwen3.5-2B Q4_K_M** và bộ đọc ảnh **mmproj-F16**. Profile Web được giữ để dùng riêng và kiểm tra hồi quy.

## Mở ứng dụng

| File tại thư mục này | Mục đích |
| --- | --- |
| `run_v2.bat` | Mở V2 Deep Learning chạy nền, chỉ hiện chấm trạng thái nhỏ. |
| `run_v2_visible.bat` | Mở V2 Deep Learning kèm cửa sổ xem ảnh, chữ đọc được, tiến trình và lỗi. |
| `open_settings.bat` | Mở Cài đặt của phiên V2, kể cả khi phím tắt gặp lỗi. |
| `run_web.bat` | Mở profile Web khi cần. |
| `check_v2.bat` | Kiểm tra môi trường và tài nguyên V2. |

**Lần chuyển sang folder mới:** nếu tool cũ còn mở, bấm **Ctrl+1** để thoát, rồi chạy `run_v2_visible.bat` trong folder này. Việc tách folder không tự thay tiến trình đang chạy. Hai bản dùng chung khóa một phiên; mở launcher mới khi bản cũ còn chạy không bảo đảm đổi sang code/profile mới.

Đây là ứng dụng chạy từ **mã Python**, hãy dùng các launcher trên. File EXE đóng gói cũ không phải bản phát triển này. Launcher ưu tiên Python trong `.venv` nếu có, sau đó dùng `%LOCALAPPDATA%\Programs\Python\Python312`; Python được chọn cần có thư viện trong `requirements.txt`.

## Dùng nhanh

1. Mở câu hỏi, để đầy đủ đề, hình và các đáp án trên màn hình.
2. Ở chế độ **Tự đọc cả vùng**, đưa chuột tới góc thứ nhất rồi bấm **Ctrl+Alt+`**; di chuột tới góc đối diện rồi bấm lại tổ hợp đó. Dấu ` là backtick/grave, thường ở bên trái số 1.
3. Đợi tool đọc ảnh, bấm **Ctrl+Enter** để giải.
4. Giữ **F7** để xem đáp án, thả để ẩn. Đáp án được copy vào Clipboard; dùng **Ctrl+V** tại nơi cần dán.
5. Câu tiếp theo giữ nguyên bố cục thì dùng lại vùng. Nếu vị trí thay đổi do cuộn trang, đổi zoom hoặc di chuyển cửa sổ, chọn lại vùng.

**Ctrl+Q** đổi giữa đọc cả vùng và vẽ riêng từng ô. Xem [toàn bộ phím tắt và cách vẽ Đề/A/B/C/D](docs/usage.md).

## Nơi chỉnh sửa

- Ứng dụng và cấu hình: [fast_v2](fast_v2/README.md).
- Model và bộ đọc ảnh: `models/`; runtime chạy model: `runtime/`; kho kiến thức: `data/`.
- Pipeline dữ liệu, đánh giá và training: `deep_learning/`.
- Phím/vùng hiện dùng: `fast_v2/ui_settings.json`. Model Deep Learning: `fast_v2/settings.deep_learning.json`; Web: `fast_v2/settings.web.json`.

Tài nguyên inference đã có ở máy thì sử dụng offline; không cần tải weights lại mỗi lần mở. Đường dẫn tài liệu môn học ngoài workspace được lưu trong profile, cần kiểm tra nếu chuyển máy.

Training là công việc riêng: môi trường training và HF weights chưa được chuẩn bị đầy đủ. Model đang chạy chưa phải model đã fine-tune riêng cho môn học. Test hồi quy hoặc báo cáo cũ không chứng minh độ chính xác 90% trên đề độc lập; cần đánh giá thực tế trước khi đưa ra kết luận đó.
