# Review và sync-back tách V2

Ngày: 2026-10-16, Asia/Saigon. Workspace: `D:/pop/study_ai_v2`.

Không phát hiện blocker trong phần thay đổi đã kiểm tra so với `source-baseline.json`.
Đã đọc AGENTS, kế hoạch, source thay đổi, launcher, doctor, installer,
test standalone, hướng dẫn và báo cáo kiểm thử/inference. Không chạy GUI,
model, tải tài nguyên hoặc sửa shortcut trong lượt review này.

## Đối chiếu nghiệm thu

- Default `fast_v2/settings.json` chọn Deep Learning; model Qwen3.5-2B, mmproj,
  runtime CUDA và knowledge nằm trong workspace mới. Test standalone xác minh
  tài nguyên của cả ba profile tồn tại và không trỏ ra ngoài workspace.
- Launcher nền/visible chọn default DL, Web chọn `settings.web.json`; launcher
  visible chuyển tiếp `%*`. Python/working directory được lấy theo launcher.
- `setup_assets.set_backend()` bỏ qua root settings không tồn tại và cập nhật
  đủ default/DL/Web; test xác minh giữ nguyên course/model. Phần import helper
  bị xóa trong DL installer không có caller sử dụng.
- Các test và benchmark Web cùng OCR smoke/DOM integration đã chọn profile Web
  tường minh. Báo cáo tester ghi full suite 60 pass, OCR và DOM đạt trước khi
  thêm test installer cuối; lượt review chạy bổ sung test standalone cuối đạt.
- `fast_v2/ui_settings.json`, `process_guard.py`, `debug_ui.py`,
  `clipboard_solver.py` khớp baseline. Phím hiện tại, hold F7/F8 và vùng chụp
  được giữ. Docs usage khớp cấu hình thực tế và xử lý chọn/vẽ vùng trong source.
- Đọc trực tiếp hai `.lnk` hiện tại bằng WScript.Shell, không Save: cả Startup
  và restart trỏ `D:/pop/study_ai_v2/fast_v2/tray_app.py`, working directory
  mới; restart có `Alt+Ctrl+W`. Backup và manifest trước sửa tồn tại trong
  `backups/20261016-shortcuts/`. Chưa thử login/hotkey vật lý.
- Đối chiếu 78 entry trong source-baseline với workspace cũ: không có mismatch.
  Việc sync-back sau đó chỉ cập nhật plan pointer cũ, không sửa source/config cũ.
- Báo cáo inference riêng của root ghi ba ca chữ/ảnh đạt, health OK và server
  test đã đóng; reviewer đọc kết quả, không chạy lại inference.
- README gốc, README ứng dụng và docs usage giải thích workspace chính, mutex,
  chuyển phiên, launcher, giới hạn training và artifact lịch sử rõ ràng.

## Kiểm tra trực tiếp trong lượt review

```text
C:/Users/vinh1/AppData/Local/Programs/Python/Python312/python.exe -m pytest fast_v2/tests/test_standalone.py -q
...                                                                      [100%]
3 passed in 0.68s
exit code: 0
```

Parse AST toàn bộ 38 file Python thuộc root, ứng dụng và DL tools: đạt.
Không ghi pyc hoặc chạy thêm full suite; lượt tester đầy đủ đã có trong
[tests.md](tests.md).

## Bằng chứng và giới hạn

- [Baseline source](source-baseline.json), [kiểm thử](tests.md),
  [inference do root chạy](standalone-inference.json), [shortcut](shortcuts.json).
- [Hướng dẫn người dùng](../../../docs/usage.md), [kế hoạch](../plan.md).
- Chưa kiểm tra GUI/hotkey vật lý, startup/login thực tế, build EXE, training,
  full benchmark hoặc độ chính xác trên bộ đề độc lập. Không suy rộng từ các
  ca smoke test thành độ chính xác toàn môn.
- Sync-back toàn kế hoạch: không có phase file; ba checklist của plan đã đủ
  bằng chứng và được đánh dấu hoàn tất ở workspace mới cùng plan pointer cũ.
  Journal skipped by preference; không commit/push.
