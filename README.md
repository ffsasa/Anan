# Anan

Anan là pipeline bản địa hóa video tự động, hướng tới việc chuyển video tiếng Trung từ URL hoặc file local thành một video tiếng Việt hoàn chỉnh.

> Trạng thái: đang ở giai đoạn thiết kế và chuẩn bị bản demo V1. Repository chưa có bản phát hành dùng được.

## V1 làm gì?

- Phát hiện các vùng có lời nói bằng VAD và nhận diện tiếng Trung.
- Dịch Trung → Việt theo ngữ cảnh.
- Sinh một giọng Việt dùng chung cho toàn bộ video.
- Đồng bộ từng câu với timeline nguồn.
- Giữ background/music/SFX thông qua source separation.
- Tạo phụ đề Việt nếu bật.
- Thêm watermark nếu bật, trong cùng lần render cuối.
- Hỗ trợ trạng thái job, retry/resume, cache và crash recovery theo thiết kế pipeline.

V1 không phân biệt người nói, không nhận diện nhân vật và không dùng voice riêng cho từng người. Đây là hướng phát triển tương lai.

## Tài liệu

- [Đặc tả sản phẩm V1](docs/product-spec.md)
- [Kiến trúc và technical baseline](docs/architecture.md)
- [DAG và hợp đồng 14 stage](docs/pipeline.md)
- [Yêu cầu phi chức năng](docs/non-functional-requirements.md)
- [Nền tảng được hỗ trợ](docs/supported-platforms.md)
- [Các quyết định kiến trúc](docs/decisions/README.md)
- [Hướng dẫn đóng góp](CONTRIBUTING.md)
- [Chính sách bảo mật](SECURITY.md)
- [Theo dõi thành phần bên thứ ba](THIRD_PARTY_NOTICES.md)

## Nguyên tắc phát triển

- Làm CLI pipeline chạy xuyên suốt trước khi hoàn thiện GUI.
- Giữ provider/model cụ thể phía sau adapter để có thể thay thế.
- Không xóa video local gốc hoặc source media hoàn chỉnh đã tải từ URL.
- Chỉ công bố `final.mp4` sau khi verify và atomic finalization thành công.
- Chốt các ngưỡng NFR, platform matrix, packaging và license trước public release sau khi có dữ liệu từ bản demo.
