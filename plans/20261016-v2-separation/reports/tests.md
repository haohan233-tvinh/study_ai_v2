# Kiểm thử workspace V2 độc lập

Ngày: 2026-10-16, Asia/Saigon. Workspace: `D:/pop/study_ai_v2`.
Python dùng cho mọi lệnh: `C:/Users/vinh1/AppData/Local/Programs/Python/Python312/python.exe`.
Tester chỉ kiểm tra và viết báo cáo; không sửa source/config/shortcut, không điều khiển GUI của người dùng, không chạy model inference, train hoặc benchmark.

## Kết quả

| Kiểm tra | Kết quả thực tế |
|---|---|
| `python -m pytest fast_v2/tests -q` | PASS, `60 passed in 35.23s`, exit 0. Gồm 58 test có sẵn và 2 test standalone. |
| `python fast_v2/tray_app.py --self-test-ocr` | PASS, exit 0. `fast_v2/artifacts/package-ocr-smoke.json`: `passed=true` cho legacy HTML, badge layout và 5 vùng thủ công; mọi `errors=[]`. |
| `python fast_v2/tests/integration_dom_extension.py` | PASS, exit 0. Chromium profile riêng và server localhost riêng đã đóng trong `finally`. |
| `python doctor_v2.py --hash`, lần đầu | FAIL, exit 1: `llama-server.exe --list-devices` quá 20 giây. Lần này trùng thời điểm pytest/OCR và root nạp DL model thật. Các dependency, hash và assets đều hợp lệ; `runtime_ok=false`, `ready=false`. |
| `python doctor_v2.py --hash`, lần kiểm lại tuần tự | PASS, exit 0, 2.60 giây: `runtime_ok=true`, `ready=true`; CUDA0 RTX 3060 Laptop GPU, 6143 MiB, 5130 MiB free. Không sửa hoặc bỏ check. |
| Tìm tham chiếu workspace cũ trong source/config/script | PASS: không có `web_app_study_ai` trong `.py/.bat/.ps1/.json` đang sử dụng, sau khi loại artifact/report/backup lịch sử và model/runtime binary. |

## Bằng chứng cụ thể

- Doctor mặc định đọc `fast_v2/settings.json`, `course=deep_learning`.
- Tất cả 10 package cần thiết có mặt; RapidOCR có 3 model ONNX.
- Model `models/deep_learning/base/Qwen3.5-2B-Q4_K_M.gguf`, 1,280,835,840 bytes, SHA-256 `aaf42c8b7c3cab2bf3d69c355048d4a0ee9973d48f16c731c0520ee914699223`, khớp manifest.
- Bộ đọc ảnh `models/deep_learning/base/mmproj-F16.gguf`, 668,227,264 bytes, SHA-256 `7035e9cb8d7c6a9681d07eef9a364783e86ea4cd73faab2eabb4f43a101830c7`, khớp manifest.
- Default DL model, mmproj, CUDA server và knowledge file đều tồn tại bên trong workspace mới. Test standalone còn xác minh tương tự cho cả `settings.json`, `settings.deep_learning.json`, `settings.web.json`.
- Test standalone xóa `STUDY_AI_PROFILE` khỏi environment của subprocess, xác nhận `ExamSolver()` mặc định tạo DL pipeline.
- DOM integration: 8 text boxes, nhận snapshot trong 0.407 giây; `capture_source=DOM`, 4 option A/B/C/D đúng nội dung; 5 vùng thủ công vẫn dùng DOM; code giữ đủ indentation và dấu ngoặc đóng.
- OCR smoke: legacy 2.720 giây; badge 3.613 giây; vùng thủ công 0.871 giây. Đây là thời gian của fixture kiểm thử, không phải cam kết hiệu năng thực tế.
- Scan rộng tìm thấy path cũ trong JSON benchmark lịch sử (`artifacts/`, `fast_v2/artifacts/`) và manifest sao lưu shortcut (`backups/20261016-shortcuts/manifest.json`). Các record này là bằng chứng quá khứ, không phải dependency runtime. `course_dir` còn trỏ thư mục học gốc ở `D:/Study/...`; đây là nguồn tài liệu ngoài workspace, không trỏ project V1.

## Giới hạn

- Chưa kiểm tra thao tác GUI, hotkey vật lý, startup/login hoặc shortcut; tester không chạm phiên đang mở của người dùng.
- Không tự chạy inference chữ/ảnh để tránh tranh VRAM với root; kết quả inference do root thực hiện cần đọc báo cáo riêng.
- Chưa xác minh độ chính xác toàn bộ môn học, training, full benchmark hoặc EXE build.
- Timeout `--list-devices` lần đầu chỉ xuất hiện trong tải đồng thời; retest tuần tự pass. Không đủ bằng chứng để coi đây là lỗi source cần sửa.
