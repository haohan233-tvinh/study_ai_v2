# Ứng dụng Study AI V2

Đây là mã ứng dụng của workspace `D:/pop/study_ai_v2`. Phát triển V2 tại đây;
bản `D:/pop/web_app_study_ai` được giữ để đối chiếu. Model, runtime và dữ liệu
nằm trong thư mục gốc của workspace mới, không cần lấy từ bản cũ.

## Mở và sử dụng

Chạy `../run_v2_visible.bat` để xem ảnh, OCR, tiến trình và lỗi; chạy
`../run_v2.bat` để dùng nền. Cấu hình mặc định `settings.json` là Deep Learning
Qwen3.5-2B Q4_K_M + mmproj-F16. `../run_web.bat` chọn Web qua `settings.web.json`.
Thoát phiên cũ bằng **Ctrl+1** trước khi chuyển workspace/profile; hai bản dùng
chung khóa một phiên để tránh tranh phím và model.

Xem [hướng dẫn sử dụng và toàn bộ phím đang lưu](../docs/usage.md).
Phím thực tế nằm trong `ui_settings.json`: **Ctrl+Enter** giải, giữ **F7** xem đáp
án, giữ **F8** xem khung, **Ctrl+Q** đổi chế độ đọc, **Ctrl+Alt+Shift+P** mở Cài
đặt, **Ctrl+1** thoát. Đưa chuột đến mỗi góc và bấm **Ctrl+Alt+grave** để chọn
vùng. **Ctrl+Alt+R** bắt đầu bộ ô Đề/A/B/C/D; **Backspace/Esc** sửa hoặc hủy lúc vẽ.

## Các phần chính

- `tray_app.py`, `debug_ui.py`: giao diện, vùng chụp, phím tắt và trạng thái.
- `clipboard_solver.py`, `prefetch.py`: điều phối đọc trước, giải và clipboard.
- `src/dl_solver.py`, `src/dl_prompt.py`: pipeline Deep Learning có ảnh.
- `src/local_model.py`: server llama.cpp local, kiểm tra RAM và dọn process.
- `src/ocr.py`, `src/layout.py`: OCR, code, chia bố cục và bộ ô thủ công.
- `web_bridge.py`, `browser_extension/`: đọc DOM tùy chọn qua loopback.
- `tests/`: hồi quy Web, DL, GUI logic, bridge và tính độc lập workspace.

## Kiểm tra khi phát triển

Dùng Python 3.12 của launcher hoặc `.venv` có các thư viện trong
`../requirements.txt`. `python` trên PATH hiện có thể trỏ sang môi trường Hermes.
Từ thư mục gốc workspace:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m pytest fast_v2/tests -q
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" doctor_v2.py --hash
```

`../check_v2.bat` chạy doctor, tests và OCR smoke. Các test/benchmark Web chọn
`settings.web.json` tường minh; mặc định sản phẩm vẫn là Deep Learning. Dùng
`../deep_learning/evaluate.py` với tập DL khi đánh giá DL, không lấy benchmark
Web làm chỉ số chất lượng DL.

Các báo cáo sao chép trong `artifacts/` là dữ liệu lịch sử. Không coi chúng là
kết quả code mới. Build EXE, training và đánh giá toàn bộ không nằm trong lần
tách workspace này. Không tự tải weights trong đường inference.
