# ADR-0001: Phạm vi speech và voice của V1

- Trạng thái: Accepted for V1
- Ngày: 2026-10-02

## Bối cảnh

Khái niệm phát hiện vùng có lời nói từng bị trộn với speaker diarization, nhận diện nhân vật và phát hiện giọng AI. Điều này khiến scope và README có thể hứa nhiều hơn pipeline V1 thực hiện.

## Quyết định

- VAD chỉ xác định các khoảng thời gian có lời nói trên timeline video nguồn.
- V1 không phân biệt, gán danh tính hoặc hợp nhất transcript theo từng người nói.
- V1 dùng một voice tiếng Việt cho toàn bộ video.
- Speaker diarization, nhận diện nhân vật, chọn voice và voice cloning theo từng người là mục tiêu tương lai.

## Hệ quả

- `recognize_speech` có thể chứa VAD như một bước con và không cần VAD port độc lập trong V1.
- Data model có thể để chỗ mở rộng cho `speaker`, nhưng pipeline không được phụ thuộc vào thông tin đó trong V1.
- Tài liệu và UI không được quảng bá multi-speaker dubbing trước khi có ADR thay thế.
