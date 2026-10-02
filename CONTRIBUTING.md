# Đóng góp cho Anan

Cảm ơn bạn quan tâm tới Anan. Dự án hiện đang ở giai đoạn thiết kế và chuẩn bị vertical-slice demo; source code và lệnh development chính thức chưa được scaffold đầy đủ.

## Trước khi đóng góp

1. Đọc [product spec](docs/product-spec.md), [architecture](docs/architecture.md) và [pipeline contracts](docs/pipeline.md).
2. Mở issue mô tả use case, expected behavior và phạm vi thay đổi.
3. Không mở rộng V1 sang diarization, multi-speaker TTS, voice cloning hoặc video editor nếu chưa có quyết định scope mới.

## Nguyên tắc code

- Domain/application không import trực tiếp code provider-specific.
- Integration mới phải nằm sau port/adapter phù hợp.
- Không sửa đè artifact revision đã commit.
- Không đặt business logic trong CLI/GUI handler.
- Không tạo `utils/`, `helpers/` hoặc folder trống nếu chưa có abstraction/code thực tế.
- Thay đổi contract phải cập nhật tài liệu và test liên quan trong cùng pull request.

## Kiểm thử

Khi source code được scaffold, pull request phải chạy các lệnh lint, type check và test được khai báo trong `pyproject.toml`. Integration test dùng model/GPU/API bên ngoài phải được đánh dấu rõ và không làm lộ credential.

## Nội dung mẫu

Chỉ đóng góp media fixture mà bạn có quyền phân phối. Ưu tiên clip ngắn, dung lượng nhỏ và có nguồn/license rõ ràng.
