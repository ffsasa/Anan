# Đặc tả sản phẩm Anan V1

> Trạng thái: thiết kế V1. Các ngưỡng định lượng sẽ được chốt sau khi có bản demo end-to-end.

## Mục tiêu

Nhận URL hoặc video local và tạo một `final.mp4` tiếng Việt, gồm nhận diện lời nói tiếng Trung, dịch theo ngữ cảnh, TTS tiếng Việt, đồng bộ timeline, giữ background/music/SFX, phụ đề tùy chọn và watermark tùy chọn.

## Luồng xử lý chính

```text
ANAN
                          │
                          ▼
                ① NHẬN VIDEO ĐẦU VÀO
                 URL hoặc file video
                          │
                          ▼
        ② KIỂM TRA MEDIA + CHUẨN BỊ WORKING ASSETS
          Không mặc định encode lại video tại bước này
                          │
                          ▼
                ③ CHUẨN BỊ ÂM THANH
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
   ④ VAD: PHÁT HIỆN VÙNG       ⑤ TÁCH GIỌNG KHỎI
      CÓ LỜI NÓI                  BACKGROUND
              │                  (default on)
              ▼                       │
   ⑥ ASR TIẾNG TRUNG                  └────► background/music/SFX
      THEO CÁC VÙNG VAD                         dùng lại khi mix
              │
              ▼
          Transcript
              │
              ▼
    ⑦ DỊCH TRUNG → VIỆT THEO NGỮ CẢNH
              │
              ▼
    ⑧ KIỂM TRA TRƯỚC TTS
      - rule/consistency/LLM khi cần
      - targeted OCR đọc frame video khi cần xác minh source
      - nếu sửa source thì dịch lại phần bị ảnh hưởng
              │
              ▼
    ⑨ TẠO GIỌNG NÓI TIẾNG VIỆT
              │
              ▼
    ⑩ KIỂM TRA THỜI LƯỢNG SAU TTS
              │
       ┌──────┴───────────────┐
       │                      │
       ▼                      ▼
  Lệch ít/vừa            Lệch quá nhiều
  trim/pad/stretch        rút gọn bản dịch
  trong giới hạn          → TTS lại có giới hạn
       │                      │
       └──────────┬───────────┘
                  ▼
    ⑪ ĐỒNG BỘ VÀ ĐẶT TỪNG CÂU
       VÀO TIMELINE VIDEO NGUỒN
                  │
                  ▼
    ⑫ MIX GIỌNG VIỆT + BACKGROUND
       + DUCKING/LOUDNESS
                  │
                  ▼
    ⑬ TẠO PHỤ ĐỀ VIỆT NẾU BẬT
                  │
                  ▼
    ⑭ RENDER VIDEO TRONG MỘT BƯỚC
       - video nguồn + audio đã mix
       - burn-in phụ đề nếu bật
       - thêm watermark nếu bật
       - verify rồi atomic publish
                  │
                  ▼
             FINAL VIDEO
```

## Giới hạn V1

- VAD chỉ phát hiện các khoảng thời gian có lời nói để hỗ trợ ASR, tạo phụ đề, đồng bộ và ghép âm thanh.
- V1 không phân biệt người nói, không gán danh tính nhân vật và chỉ dùng một voice tiếng Việt.
- Speaker diarization, nhận diện nhân vật và chọn/clone voice riêng cho từng người là hướng phát triển tương lai, không thuộc DAG V1.

## Trong phạm vi V1

1. URL hoặc local video → một MP4 Việt cuối cùng.
2. Download và phân tích media tự động.
3. Extract/chuẩn bị audio.
4. ASR tiếng Trung.
5. VAD chỉ để phát hiện các vùng có lời nói và giữ timestamp trên timeline video nguồn; không phân biệt người nói.
6. Source separation để giữ background/music/SFX.
7. Dịch Trung → Việt có context.
8. Pre-TTS validation:
   - rule;
   - consistency;
   - semantic validation bằng LLM khi cần;
   - dub-length estimation.
9. Targeted OCR verification:
   - khi ASR đáng ngờ;
   - tên riêng đáng ngờ;
   - validator yêu cầu;
   - hoặc user bật.
10. Vietnamese TTS một voice dùng chung cho toàn bộ video.
11. Post-TTS validation:
    - duration;
    - silence;
    - overlap;
    - khả năng fit timeline.
12. Feedback loop:
TTS quá dài
↓
rút gọn translation
↓
TTS lại

13. Time alignment/sync.
14. Ghép voice Việt + background.
15. Loudness normalization.
16. Subtitle Việt optional.
17. Watermark optional, được xử lý cùng stage render cuối; không tạo một lần encode riêng.
18. MP4 final được verify trước khi công bố.
19. Progress từng stage.
20. Cancel job.
21. Retry từ stage lỗi.
22. Cache cho failed job.
23. Auto-cleanup sau success.
24. PySide6 GUI sau khi CLI pipeline ổn.

## Ngoài phạm vi V1

Các mục sau không thuộc V1 nhưng có thể là hướng phát triển tương lai:
- Automatic speaker diarization/phân biệt người nói.
- Gán danh tính người nói hoặc nhân vật.
- Multi-speaker TTS.
- Tự chọn giọng nam/nữ/già/trẻ theo từng người hoặc nhân vật.
- Voice cloning riêng cho từng người hoặc nhân vật.
Lip-sync.
Nhận diện khuôn mặt/nhân vật.
Full-video OCR mọi frame.
Manual subtitle editor.
Timeline editor.
Video editor kiểu Premiere.
Batch cả series.
Queue nhiều video chạy đồng thời.
Multi-language translation.
*Auto thumbnail.
*Auto title/description/tags.
*Auto upload YouTube.
Cloud backend/server.
Multi-user/account system.
Mobile/macOS/Linux support chính thức.
Training/fine-tuning model.
DRM bypass.
Model marketplace/model manager phức tạp.

## Tài liệu liên quan

- [Kiến trúc](architecture.md)
- [DAG và hợp đồng các stage](pipeline.md)
- [Yêu cầu phi chức năng](non-functional-requirements.md)
- [Nền tảng được hỗ trợ](supported-platforms.md)
- [Các quyết định kiến trúc](decisions/README.md)

