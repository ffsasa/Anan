# Yêu cầu phi chức năng

Trạng thái: các NFR dưới đây là định hướng sơ bộ cho V1. Sau khi có bản demo end-to-end, dự án sẽ benchmark, bổ sung tiêu chí đo được, chỉnh lại NFR và mới áp dụng đầy đủ vào code. Riêng các nguyên tắc an toàn dữ liệu đầu vào và crash recovery dưới đây phải được giữ ngay từ đầu.

## NFR-01 — Reliability
Mỗi stage phải có đúng một trạng thái tại một thời điểm:
PENDING
RUNNING
SUCCESS
FAILED
SKIPPED
CANCELLED
INTERRUPTED
Không có trạng thái mơ hồ.
Job crash không được làm mất toàn bộ progress.

### Crash recovery
- Khi khởi động, engine kiểm tra các job/stage còn RUNNING nhưng không còn worker hợp lệ và chuyển chúng sang INTERRUPTED.
- Output chỉ được tái sử dụng nếu artifact đã ghi xong, validate và commit đầy đủ. File trong attempt dở không được coi là output thành công.
- Engine giữ lại các revision đã commit còn hợp lệ, bỏ qua hoặc dọn attempt chưa commit, rồi lập kế hoạch chạy tiếp từ stage đầu tiên bị gián đoạn hoặc có input/output không hợp lệ.
- Không chạy lại các nhánh độc lập còn hợp lệ và không trộn artifact thuộc các revision khác nhau.
- Việc cập nhật stage state, artifact manifest và con trỏ revision phải bền vững/atomic ở mức cần thiết để lần khởi động sau xác định được trạng thái thật.
- Nếu không còn input hợp lệ để phục hồi, báo rõ job không thể tiếp tục và cần chạy lại từ đầu; không âm thầm thay nguồn.

## NFR-02 — Retry / Resume
Mỗi stage phải có input/output contract rõ.

## NFR-03 — Idempotency
Chạy lại cùng một stage với cùng input/config phải không phá job state.
Không được kiểu:
Retry TTS
→ audio cũ + audio mới bị mix chồng
Stage phải thay thế output của chính nó một cách kiểm soát.

## NFR-04 — Một visible output

## NFR-05 — Cleanup
SUCCESS
→ xóa large temp do job tạo theo policy
FAILED
→ giữ tối đa 24h
CANCEL
→ cleanup mặc định

### Quy tắc bảo vệ input
- Không bao giờ xóa file video local gốc do người dùng chọn.
- Không xóa thông tin URL nguồn khỏi job record.
- Source media hoàn chỉnh đã tải từ URL cũng được xem là input được bảo vệ và không bị auto-cleanup; nếu sau này muốn cho phép xóa phải có policy/tùy chọn riêng được thiết kế rõ.
- Cleanup chỉ được xóa artifact tạm do job sở hữu và phải bảo toàn input, final.mp4 cùng metadata cần cho lịch sử/khôi phục.

## NFR-06 — Atomic finalization
final.tmp.mp4
      ↓
verify
      ↓
atomic rename
      ↓
final.mp4

## NFR-07 — UI responsiveness
UI không bao giờ chạy:
ASR
Demucs
TTS
FFmpeg render
	trực tiếp trên UI thread.
UI phải tiếp tục:
responsive
progress update
cancel
show error
	trong suốt job.

## NFR-08 — Resource control
Không cố song song GPU chỉ vì dependency cho phép.
Parallelism chỉ áp dụng khi resource scheduler xác nhận an toàn.

## NFR-09 — Không encode video thừa

## NFR-10 — Error reporting
Phải biết:
Job 37
Stage: TTS
Segment: 428
Error: ...

## NFR-11 — Reproducibility
Phải pin:
Python package versions
model identifiers
model hashes/version
FFmpeg version khi release

## NFR-12 — Security
API key không commit vào repository.
Ứng dụng release nên lưu credential bằng OS credential store thay vì plaintext nếu có thể.
Logs không được vô tình lộ thông tin.

## NFR-13 — Adapter isolation
Pipeline không được import trực tiếp provider-specific code

## NFR-14 — Testability
Mỗi stage phải chạy/test độc lập được.

## Trạng thái áp dụng

Các NFR hiện là định hướng thiết kế. Sau khi có demo end-to-end, dự án phải benchmark, bổ sung tiêu chí đo được và cập nhật lại tài liệu này trước khi coi chúng là acceptance criteria chính thức.

