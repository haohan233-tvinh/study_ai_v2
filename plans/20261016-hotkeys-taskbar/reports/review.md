# Review sửa hotkey và vị trí chấm trạng thái

Ngày: 2026-10-16. Review độc lập theo `akk-code-review`, chỉ đọc source/UI/config;
không hook hoặc gửi phím vào phiên người dùng, không nạp model, không chạy lặp
full suite đang do tác nhân chính phụ trách.

## Kết luận

Không còn finding chặn trong phạm vi đã review sau vòng sửa dưới đây.
Source phù hợp phạm vi: action chuyển sang Windows `RegisterHotKey`, hold F7/F8
giữ luồng hiện có, callback defer sang Qt trước modal; Settings có launcher/IPC;
chấm dùng work area với khoảng cách 6 px logic. Không thay model, phím đã lưu
hay vùng chụp. `ui_settings.json` hiện tại bằng nội dung snapshot trước sửa.

## Finding đã sửa và kiểm chứng lại

**[P1] Không để lỗi đăng ký phím thoát khỏi callback đóng Settings.**
Trước vòng sửa review, nhánh Cancel gọi `bind_keys()` ngoài guard; nhánh rollback
cũng làm tương tự. Với action native, xung đột với ứng dụng khác là lỗi
`OSError(1409)` hợp lệ. Cấu hình có xung đột vẫn mở được bằng `--settings`,
nhưng Cancel khi đăng ký lại gây exception thoát Qt callback, giữ `editing=True`
và không ghi `settings_closed`; exception thoát Python Qt slot có thể làm dừng app.

Tái hiện bằng fake `SettingsDialog.exec=Rejected`, fake `bind_keys` phát
`OSError(1409)`; không cần GUI/hook/WinAPI thật. Kết quả trước sửa: exception
thoát, `editing=True`, không có sự kiện đóng. Bản sửa thêm
`TrayApp._rebind_or_notify()` và dùng tại Cancel lẫn rollback. Chạy lại cùng
reproduction trên source sau sửa: không exception, `editing=False`, có
`settings_closed`, thông báo chỉ tới `open_settings.bat`. Regression test
`test_cancel_settings_with_hotkey_collision_keeps_app_recoverable` giữ đường này.

## Phạm vi đã đọc

- So snapshot `backups/20261016-hotkeys-taskbar/tray_app.py` và `debug_ui.py`
  với source hiện tại; kiểm tra cấu hình trước/sau.
- `fast_v2/src/windows_hotkeys.py`: parser, giới hạn ID và tái sử dụng, thread Qt,
  WM_HOTKEY filtering, remover idempotent/retry, lỗi đăng ký và cleanup.
- `fast_v2/tray_app.py`: bind/unbind, callback deferred, Settings Cancel/rollback,
  đường `--settings`/single-instance IPC và vị trí dialog.
- `fast_v2/debug_ui.py`: `availableGeometry`, màn hình chứa vùng chụp, DPI,
  tọa độ màn hình âm và khoảng cách chấm.
- Các test native/Qt/workarea và `open_settings.bat`, `docs/usage.md`.

## Giới hạn chứng cứ

Full suite và live UI thuộc tác nhân chính; báo cáo này không coi kết quả tác nhân
khác là kiểm thử trực tiếp của reviewer. Reproduction của reviewer chỉ kiểm tra
đường lỗi/recovery bằng mocks. AnyDesk thật, bàn phím vật lý, taskbar tự ẩn và
nhiều màn hình thật chưa được reviewer thao tác. Test fake work area gồm tọa độ
âm/DPI không thay thế xác minh trên phần cứng đó.
