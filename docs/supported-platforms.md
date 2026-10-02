# Nền tảng được hỗ trợ

> Trạng thái: chưa chốt. Tài liệu này sẽ được hoàn thiện sau bản demo end-to-end và trước public release.

## Baseline hiện tại

- Runtime: Python 3.11.
- Loại ứng dụng: CLI trước, desktop GUI sau.
- CPU và GPU phải dùng chung pipeline contract; khác biệt implementation nằm sau adapter/configuration.
- Mobile không thuộc V1.
- macOS và Linux chưa được cam kết hỗ trợ chính thức trong V1.

Các dòng trên là định hướng thiết kế, không phải cam kết rằng installer hiện đã hoạt động.

## Cần benchmark sau demo

| Hạng mục | Trạng thái |
|---|---|
| Windows version/architecture | TBD |
| CPU-only support | TBD |
| NVIDIA GPU/CUDA matrix | TBD |
| RAM tối thiểu/khuyến nghị | TBD |
| VRAM tối thiểu/khuyến nghị | TBD |
| Dung lượng cài đặt và model cache | TBD |
| Codec/container đầu vào | TBD |
| Duration/resolution tối đa đã kiểm thử | TBD |
| FFmpeg/eSpeak NG cài riêng hay bundle | TBD |
| Installer/portable package | TBD |
| Model download, checksum và offline behavior | TBD |

Chỉ chuyển một dòng từ `TBD` sang `Supported` sau khi có test hoặc benchmark tái lập được. Môi trường chưa kiểm thử phải ghi rõ là `Best effort` hoặc `Unsupported`, không suy diễn từ khả năng lý thuyết của dependency.
