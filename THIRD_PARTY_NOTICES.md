# Third-party components and model notices

> Trạng thái: inventory sơ bộ, chưa phải bản license audit cuối cùng và chưa đủ để phân phối release binary.

Anan dự kiến tích hợp các thành phần sau qua dependency, executable, model weights hoặc remote API:

| Thành phần | Vai trò | Cách sử dụng dự kiến | License/review |
|---|---|---|---|
| Python | Runtime | Cài đặt/đóng gói | TBD trước release |
| uv | Dependency management | Development/install | TBD trước release |
| Typer | CLI | Python dependency | TBD trước release |
| PySide6/Qt | Desktop GUI | Python/Qt binaries | TBD trước release |
| yt-dlp | Download | Dependency/executable | TBD trước release |
| FFmpeg/FFprobe | Media processing | External binaries hoặc bundle | Build cụ thể phải được audit |
| Pydantic | Data model/validation | Python dependency | TBD trước release |
| SenseVoiceSmall/FunASR | ASR/VAD | Code và model weights | Audit code và weights riêng |
| faster-whisper | ASR fallback | Code và model weights | Audit code và weights riêng |
| demucs-infer/HTDemucs | Source separation | Code và model weights | Audit code và weights riêng |
| PaddleOCR/OpenCV | Targeted OCR | Code và model weights | Audit code và weights riêng |
| LLM provider | Translation/conditional validation | Remote API | Terms, privacy và data flow TBD |
| VieNeu-TTS 0.5B | Vietnamese TTS | Code và model weights | Audit code, weights và voice assets riêng |
| pysubs2 | ASS subtitle | Python dependency | TBD trước release |
| PyInstaller hoặc packaging tool thay thế | Packaging | Build-time tool | Chỉ chốt sau packaging spike |

## Release gate

Trước public release phải:

- pin chính xác package version, model ID/revision và nguồn tải;
- xác minh license của code, model weights, dataset-derived asset, font, icon và sample media;
- xác định thành phần nào được bundle và thành phần nào tải lúc runtime;
- kèm đầy đủ license text, attribution và source offer/link nếu license yêu cầu;
- kiểm tra FFmpeg build flags/codec thay vì chỉ ghi chung là “FFmpeg”;
- thay thế component qua adapter nếu điều khoản không phù hợp với mục tiêu phát hành.

Không đưa API key, access token hoặc cookie vào notice, manifest public hay release artifact.
