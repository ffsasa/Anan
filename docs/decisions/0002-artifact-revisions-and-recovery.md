# ADR-0002: Artifact revision và recovery

- Trạng thái: Accepted for V1
- Ngày: 2026-10-02

## Bối cảnh

Video và audio có thể rất lớn; retry hoặc crash không được làm mất toàn bộ tiến độ, trộn output cũ/mới hoặc bắt người dùng quản lý cache thủ công.

## Quyết định

- Artifact được nhận diện bằng `artifact_id` và `revision`.
- Output mới được ghi trong vùng attempt riêng, validate rồi mới commit.
- Revision đã commit không bị sửa đè.
- Cache key tham chiếu đúng input revision, cấu hình liên quan và provider/model/tool thực tế.
- Resume chỉ tái sử dụng output đã commit và còn hợp lệ; attempt dở không phải output thành công.
- File local gốc và source media hoàn chỉnh tải từ URL là protected input, không thuộc auto-cleanup.

## Hệ quả

- Pipeline có thể khôi phục tối thiểu nhánh bị lỗi và giữ nhánh độc lập còn hợp lệ.
- Registry/manifest phải lưu provenance và ownership đủ để kiểm tra reuse/cleanup.
- Chi tiết đầy đủ nằm trong [pipeline.md](../pipeline.md).
