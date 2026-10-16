---
title: "Tách V2 thành workspace phát triển độc lập"
status: completed
created: 2026-10-16
priority: P1
---

# Tách V2 thành workspace phát triển độc lập

## Kết quả và ràng buộc

Tạo `D:/pop/study_ai_v2` gồm source V2, test/fixture, dữ liệu, model và CUDA runtime
cục bộ. Giữ layout `fast_v2/` để bảo toàn đường dẫn các công cụ DL. Bản mới mặc
định Deep Learning, có launcher rõ ràng, giữ nguyên phím/vùng đã lưu. Giữ bản cũ
làm snapshot; từ nay source mới là nơi phát triển V2. Không đổi thuật toán,
không huấn luyện, không commit/push, không đưa network audit sang V2.

## Scout và quyết định

- Python 3.12 + PyQt6, OCR/retrieval + llama.cpp CUDA; inference offline.
- App và DL tools có đường dẫn tương đối xuyên `fast_v2/`, `models/`, `data/`, `runtime/`.
- Cả tests Web và DOM integration đang ngầm dựa default Web; cần chọn profile Web
  rõ trong các bài kiểm tra đó khi default sản phẩm chuyển sang DL.
- Runtime dùng chung mutex để tránh hai bản cùng chiếm hotkey; không cho chạy song song.
- Shortcut Startup và Ctrl+Alt+W cần trỏ sang bản mới; kiểm tra và sao lưu trước khi cập nhật.
- Chỉ sao chép file hoàn chỉnh, không kéo build/EXE cũ, cache hoặc model training tải dở.
- Review kế hoạch: giữ layout nội bộ giảm thay đổi API; copy riêng asset tránh phụ thuộc
  bản cũ; kiểm tra profile, checksum, test và model thật là điều kiện bàn giao.

## Các bước

- [x] Sao chép source/asset hoàn chỉnh sang workspace mới, xác minh không phụ thuộc bản cũ.
- [x] Đặt default DL, thêm launcher/hướng dẫn/AGENTS cho V2 và cập nhật shortcut có backup.
- [x] Test V2, kiểm tra OCR/DOM và inference thật từ thư mục mới; review độc lập.

## Tiêu chí nghiệm thu

- Model/runtime/data của mọi profile đi kèm nằm trong workspace mới, checksum model hợp lệ.
- Đọc settings mặc định cho ra DL; launcher nền/visible/restart đều mở workspace mới.
- Phím và chế độ hold F7/F8 giữ đúng cấu hình hiện tại; hướng dẫn khớp file đã lưu.
- Test Web regression dùng explicit profile và đạt; DL inference chữ/ảnh thật đạt.
- Source V1/bản cũ và các thay đổi chưa commit có sẵn không bị ghi đè hoặc xóa.
- Ghi rõ việc chưa kiểm tra GUI/hotkey vật lý và các giới hạn training/benchmark.

## Hoàn tất và bằng chứng

Hoàn tất 3/3 bước ngày 2026-10-16. Workspace phát triển chính:
`D:/pop/study_ai_v2`; bản cũ giữ làm snapshot.

- [Review và sync-back](reports/review.md), [test/OCR/DOM](reports/tests.md).
- [Inference chữ/ảnh](reports/standalone-inference.json),
  [shortcut hiện tại](reports/shortcuts.json), [baseline source](reports/source-baseline.json).
- [Cách sử dụng và phím tắt](../../docs/usage.md).

Chưa kiểm tra GUI/hotkey vật lý hoặc startup/login thực tế. Chưa training,
build EXE, full benchmark hay đánh giá độ chính xác toàn môn. Không commit/push.
