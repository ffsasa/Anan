# Architecture Decision Records

ADR ghi lại quyết định có ảnh hưởng dài hạn tới scope, kiến trúc hoặc contract. Mỗi ADR là lịch sử quyết định; nếu thay đổi hướng đi, tạo ADR mới thay vì âm thầm sửa lý do cũ.

| ADR | Trạng thái | Quyết định |
|---|---|---|
| [0001](0001-v1-speech-and-voice-scope.md) | Accepted for V1 | VAD chỉ phát hiện vùng lời nói; V1 dùng một voice |
| [0002](0002-artifact-revisions-and-recovery.md) | Accepted for V1 | Artifact immutable theo revision; retry/resume dựa trên output đã commit |
| [0003](0003-single-pass-final-render.md) | Accepted for V1 | Subtitle và watermark tùy chọn được xử lý trong stage render cuối |

Technical stack cụ thể hiện được theo dõi trong [architecture.md](../architecture.md). Các lựa chọn model/packaging chỉ nên thành ADR khi đã được benchmark và chốt.
