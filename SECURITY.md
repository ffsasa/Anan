# Security Policy

Anan đang ở giai đoạn thiết kế/pre-release. Chưa có phiên bản production được hỗ trợ.

## Báo cáo lỗ hổng

Không đăng API key, token, cookie, đường dẫn cá nhân, transcript riêng tư hoặc video mẫu có bản quyền lên public issue.

Cho tới khi repository công bố kênh báo cáo riêng, hãy mở một issue không chứa chi tiết nhạy cảm để yêu cầu kênh liên hệ bảo mật. Maintainer sẽ cập nhật tài liệu này trước public release với phương thức báo cáo cụ thể.

## Nguyên tắc bắt buộc

- Không commit credential vào repository.
- Log và error report phải redact API key, token, cookie và dữ liệu nhạy cảm.
- Gọi executable bên ngoài bằng argument list an toàn; không ghép input người dùng thành shell command.
- Validate URL, local path và media metadata trước khi xử lý.
- Không xóa hoặc sửa video local gốc của người dùng.
- Source media hoàn chỉnh tải từ URL được đánh dấu protected input và không thuộc auto-cleanup.
- Output tạm chưa commit không được downstream tin cậy.
- Chỉ công bố `final.mp4` sau verify và atomic finalization.

Threat model chi tiết, secret storage cho GUI/CLI và chính sách dữ liệu gửi tới LLM API sẽ được chốt trước public release.
