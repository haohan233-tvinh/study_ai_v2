# Hướng dẫn phát triển V2

- Làm việc tại `D:\pop\study_ai_v2`. Giữ `D:\pop\web_app_study_ai` làm snapshot; không sửa bản đó khi phát triển V2 trừ khi người dùng yêu cầu.
- Ưu tiên luồng Deep Learning với Qwen3.5-2B + mmproj. Giữ profile Web dùng được; khi sửa phần dùng chung, kiểm tra hồi quy bằng profile Web được chọn tường minh, tránh để test Web vô tình chạy với default Deep Learning.
- Giữ cấu hình cá nhân trong `fast_v2/ui_settings.json`, đặc biệt phím tắt và vùng chụp. Không ghi đè bằng giá trị mặc định khi sửa launcher hoặc di chuyển workspace.
- Chạy từ mã Python qua launcher hiện hành. Không dùng EXE cũ làm bằng chứng cho code mới. Hai workspace dùng chung khóa một phiên; không khởi chạy GUI thứ hai rồi giả định đã chuyển bản khi bản cũ còn chạy.
- Không tải model/HF weights trong đường chạy inference. Chuẩn bị tài nguyên, training và inference là các bước riêng; không coi GGUF inference là HF weights cho training.
- Với thay đổi code, chạy test nhỏ nhất chứng minh phần bị ảnh hưởng trước, rồi kiểm tra các caller dùng chung. Dùng `check_v2.bat` để kiểm tra môi trường; nó không thay thế kiểm thử chức năng hoặc lần chạy model thật.
- Báo cáo chính xác phần đã chạy và phần chưa kiểm chứng. Các file `artifacts/`, log và báo cáo được sao chép từ snapshot chỉ là chứng cứ lịch sử. Không suy ra độ chính xác 90% từ test tự tạo.
- Cập nhật [docs/usage.md](docs/usage.md) khi thay đổi thao tác hoặc phím người dùng; lấy cấu hình thực tế và source làm căn cứ. Không tự commit, push, publish hay tải lại model ngoài yêu cầu hiện tại.
