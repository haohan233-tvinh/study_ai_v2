---
title: "Sửa phím tắt và chấm trạng thái trên taskbar"
status: completed
created: 2026-10-16
---

# Sửa phím tắt và chấm trạng thái

## Phạm vi

Khôi phục mở Cài đặt/các action shortcuts, giữ nguyên phím và vùng người dùng;
chấm ở góc phải dưới của vùng làm việc phía trên taskbar. Không đổi model,
không sửa package keyboard cài toàn máy, không thay source bản cũ.

## Chẩn đoán đã tái hiện

- Phiên mới đúng workspace; Ctrl+Enter có log kết quả thật. Không có Settings
  window sau thử Ctrl+Alt+Shift+P bằng SendInput.
- `_winkeyboard.prepare_intercept` bỏ primary P có flags injected+Alt (0x30),
  trong khi physical0 và injected0x10 đi qua: regression cô lập không hook OS.
- `keyboard.add_hotkey` exact-match toàn bộ pressed keys: giữ F7/F8 thì các
  action không khớp, thả hold thì hoạt động lại: regression cô lập.
- StatusDot dùng `screen.geometry()` nên đặt ở y1075..1080, trong khi work area
  primary kết thúc ở1032. `availableGeometry()` giải quyết trực tiếp.

## Phương án đã review

Action dùng RegisterHotKey + Qt native event filter, giữ hook cho hold F7/F8 và
mouse. Không monkeypatch keyboard toàn máy. Giữ cleanup/unbind, phát hiện xung
đột đăng ký. Thêm lối mở Settings trực tiếp từ launcher để khôi phục khi cần.
Đổi geometry chấm sang work area, vẫn giữ kích thước và loại khỏi screenshot.

## Các bước và nghiệm thu

- [x] Native action hotkeys, regression (routing, repeat, unregister/rebind, collision).
- [x] Chấm nằm trọn work area phía trên taskbar; mở Settings có đường trực tiếp.
- [x] Test affected suite + review, restart đúng phiên V2 và kiểm chứng live Settings.

Không claim test giả lập là phím vật lý. Ghi riêng kết quả UI/SendInput live và
phần chưa xác minh. Giữ snapshot source/config trước sửa và restart đúng process.

## Kết quả

Full suite: 79 passed, 44 subtests passed trong 35.29 giây. Review độc lập không
còn blocker sau sửa guard Cancel/rollback khi tổ hợp đã bị ứng dụng khác chiếm.
Đã thử live Ctrl+Alt+Shift+P mở Cài đặt lại sau Cancel, Ctrl+Q đổi auto/manual rồi
trở lại auto, và --settings IPC mở cửa sổ trong phiên đang chạy. Người dùng xác
nhận sử dụng AnyDesk; thử live dùng SendInput, không coi là xác minh bàn phím vật lý.
Chấm thực tế ở [1909,1021,1914,1026], taskbar bắt đầu y1032.
Phiên cuối PID28616 khởi động sau lần sửa source cuối và cửa sổ Cài đặt đang hiện.

Bằng chứng: [review](reports/review.md), [kiểm chứng live](reports/live-verification.json),
[báo cáo hoàn tất](reports/completion.md). Không commit/push; không journal tự động.
