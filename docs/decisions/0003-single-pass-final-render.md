# ADR-0003: Render cuối trong một stage

- Trạng thái: Accepted for V1
- Ngày: 2026-10-02

## Bối cảnh

Burn subtitle và thêm watermark ở các stage riêng sau khi tạo video có thể khiến video bị encode nhiều lần, làm tăng thời gian xử lý và giảm chất lượng.

## Quyết định

`render_video` chịu trách nhiệm:

- mux/encode source video với mixed audio;
- burn subtitle khi bật;
- thêm watermark khi bật;
- kết hợp các filter hình ảnh trong cùng một lần encode khi cần;
- verify candidate và atomic publish thành `final.mp4`.

Subtitle và watermark đều optional. Không tạo stage watermark riêng trong V1.

## Hệ quả

- Thay đổi watermark chỉ invalidate `render_video` và `cleanup` trong một yêu cầu xử lý mới.
- Khi không cần filter/re-encode và container cho phép, implementation có thể stream copy theo policy.
- Output không được công bố nếu verify thất bại.
