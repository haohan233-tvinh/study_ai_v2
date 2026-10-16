# Hoàn tất sửa phím và chấm trạng thái V2

Ngày 2026-10-16. Chỉ sửa workspace `D:/pop/study_ai_v2`.

- Action shortcuts dùng Windows RegisterHotKey, tránh bộ lọc injected+Alt của
  keyboard cũ và khớp sai khi giữ F7/F8. Giữ nguyên các phím đã lưu.
- Hold F7/F8 và mouse giữ luồng riêng; không sửa thư viện keyboard toàn máy.
- Chấm dùng availableGeometry và cách taskbar 6 px logic, kiểm tra gồm màn hình
  có tọa độ âm và DPI2. Quan sát thật: chấm kết thúc y1026, work area kết thúc1032.
- Cài đặt được đưa lên màn hình đặt chuột; thêm `open_settings.bat` và IPC dùng
  lại phiên. Callback được defer trước modal; xung đột đăng ký khi Cancel/rollback
  được báo thay vì làm app thoát hoặc giữ editing=True.
- Test cuối: `Python312/python.exe -m pytest fast_v2/tests -q`:
  **79 passed, 44 subtests passed in 35.29s**. Review độc lập đạt sau sửa guard.
- Live: đóng Cài đặt bằng Cancel, tổ hợp Ctrl+Alt+Shift+P mở lại; Ctrl+Q đổi sang
  manual rồi auto; --settings mở cửa sổ trong phiên đang chạy. Cấu hình phím giữ nguyên.
- PID cuối28616 chạy source sau lần sửa cuối; đã mở sẵn Cài đặt bằng IPC.
- Bàn phím vật lý, mọi hành vi AnyDesk và hold F7/F8 đồng thời phím khác chưa được
  thử đầy đủ trực tiếp. Tái hiện bộ lọc Alt và routing được kiểm tra cô lập; không
  khẳng định toàn bộ đường phím từ xa đều đã được thao tác.

Snapshot trước sửa ở `backups/20261016-hotkeys-taskbar/`. Không đổi model, không
commit/push, không journal. Tài liệu tại `docs/usage.md` đã cập nhật đường mở Cài đặt.
