# Kiến trúc Anan

> Anan là modular monolith theo hướng Ports and Adapters. CLI, GUI và worker dùng chung application core; integration cụ thể nằm sau các port.

## Technical baseline

| 	Thành phần 	| 		Chốt 			| 		Ghi chú 									|
|-----------------------|---------------------------------------|-----------------------------------------------------------------------------------------------|
| Ngôn ngữ 		| **Python 3.11** 			| Core của toàn bộ Anan 									|
| Dependency 		| **uv + `pyproject.toml`** 		| Lock dependency rõ ràng, uv cài thư viện, pyproject.toml ghi rõ dependency 			|
| CLI 			| **Typer** 				| Làm engine chạy được trước GUI 								|
| Desktop UI 		| **PySide6** 				| GUI Dudu-style sau khi CLI ổn 								|
| Download 		| **yt-dlp** 				| URL → media 											|
| Media inspection 	| **FFprobe** 				| Đọc stream, codec, duration... đọc thông tin kỹ thuật của file media.				|
| Media processing 	| **FFmpeg** 				| Audio, mix, sync, encode, mux... thực sự xử lý video/audio. Chuẩn hóa video			|
| Data model 		| **Pydantic** 				| Để định nghĩa cấu trúc dữ liệu, kiểm tra có đúng kiểu dữ liệu không				|
| Job state 		| **SQLite** 				| Stage status, retry, lịch sử nhỏ 								|
| Pipeline 		| **Custom DAG / state machine** 	| Không cần Celery/Airflow, người điều phối flow						|
| ASR chính 		| **SenseVoiceSmall qua FunASR** 	| Ưu tiên bài toán tiếng Trung 									|
| ASR dự phòng		| **faster-whisper** 			| Qua cùng `SpeechRecognizer` adapter 								|
| VAD 			| **FSMN-VAD / FunASR** 		| Xác định vùng có lời nói 									|
| Separation 		| **demucs-infer / HTDemucs** 		| Qua `Separator` adapter, tách nguồn âm thanh background và vocal				|
| OCR 			| **PaddleOCR + OpenCV** 		| Chỉ targeted/smart OCR 									|
| Translation 		| **LLM API qua `Translator` adapter** 	| Structured JSON 										|
| Validation 		| **Python rules + LLM khi cần** 	| Không gọi LLM cho mọi kiểm tra 								|
| TTS 			| **VieNeu-TTS 0.5B** 			| Local Vietnamese TTS 										|
| Audio sync 		| **FFmpeg** 				| silence trim/pad + `atempo`, ép từng câu TTS Việt nằm đúng khoảng thời gian của segment gốc	|
| Audio mix 		| **FFmpeg** 				| mix, ducking, loudness, lấy background + TTS Việt rồi tạo ra track âm thanh cuối cùng		|
| Subtitle 		| **ASS + pysubs2** 			| Burn-in mặc định nếu bật sub 									|
| Logging 		| **Python `logging`** 			| Job/stage log 										|
| Test 			| **pytest** 				| Unit + stage integration tests 								|
| Packaging 		| **PyInstaller** 			| Chỉ làm sau khi engine ổn 									|

## Các quyết định để sau demo

- Ma trận hệ điều hành, CPU/GPU, RAM/VRAM, dung lượng, codec, quy trình cài đặt và đóng gói sẽ được benchmark và chốt sau khi có bản demo chạy xuyên suốt.
- Các ngưỡng chất lượng/hiệu năng chi tiết của NFR sẽ được đo trên bản demo rồi mới chốt và áp dụng vào code.
- Việc rà soát license của thư viện, model, model weights và bản FFmpeg phân phối sẽ thực hiện trước khi public release. Nếu một công nghệ không phù hợp, thay adapter/implementation nhưng giữ nguyên contract và logic pipeline.

## Tổng quan và cấu trúc repository

```text
ONE REPOSITORY
                    ANAN
                     │
        ┌────────────┼────────────┐
        │            │            │
       CLI          GUI         Worker
        │            │            │
        └────────────┴────────────┘
                     │
               Application Core
                     │
                   Domain
                     │
                  Adapters

Anan/
│
├── pyproject.toml
├── uv.lock
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
│
├── docs/
│   ├── architecture.md
│   └── adr/
│
├── src/
│   └── anan/
│       │
│       ├── __init__.py
│       ├── __main__.py
│       │
│       ├── bootstrap.py
│       ├── config.py
│       │
│       ├── domain/ (Lõi)
│       │   ├── __init__.py
│       │   │
│       │   ├── models/
│       │   │   ├── job.py
│       │   │   ├── media.py
│       │   │   ├── segment.py
│       │   │   ├── transcript.py
│       │   │   └── artifact.py
│       │   │
│       │   ├── enums.py
│       │   ├── errors.py
│       │   │
│       │   └── policies/
│       │       ├── sync_policy.py
│       │       ├── retry_policy.py
│       │       └── cleanup_policy.py
│       │
│       ├── application/ (Lõi)
│       │   │
│       │   ├── ports/ (Port đầu ra)
│       │   │   ├── downloader.py
│       │   │   ├── media_inspector.py
│       │   │   ├── media_processor.py
│       │   │   ├── speech_recognizer.py
│       │   │   ├── separator.py
│       │   │   ├── translator.py
│       │   │   ├── ocr_engine.py
│       │   │   ├── tts_engine.py
│       │   │   ├── job_repository.py
│       │   │   └── artifact_store.py
│       │   │
│       │   ├── use_cases/
│       │   │   ├── run_job.py
│       │   │   ├── retry_stage.py
│       │   │   ├── cancel_job.py
│       │   │   └── clean_cache.py
│       │   │
│       │   └── pipeline/
│       │       ├── engine.py
│       │       ├── graph.py
│       │       ├── context.py
│       │       ├── stage.py
│       │       │
│       │       └── stages/
│       │           ├── ingest.py
│       │           ├── inspect_media.py
│       │           ├── prepare_audio.py
│       │           ├── recognize_speech.py
│       │           ├── separate_audio.py
│       │           ├── translate.py
│       │           ├── validate_pre_tts.py
│       │           ├── synthesize_speech.py
│       │           ├── validate_post_tts.py
│       │           ├── synchronize.py
│       │           ├── mix_audio.py
│       │           ├── build_subtitles.py
│       │           ├── render_video.py
│       │           └── cleanup.py
│       │
│       ├── adapters/(Adapter đầu ra)
│       │   │
│       │   ├── download/
│       │   │   └── yt_dlp_downloader.py
│       │   │
│       │   ├── media/
│       │   │   ├── ffprobe_inspector.py
│       │   │   └── ffmpeg_processor.py
│       │   │
│       │   ├── asr/
│       │   │   ├── sensevoice_recognizer.py
│       │   │   └── faster_whisper_recognizer.py
│       │   │
│       │   ├── separation/
│       │   │   └── demucs_separator.py
│       │   │
│       │   ├── translation/
│       │   │   └── llm_translator.py
│       │   │
│       │   ├── ocr/
│       │   │   └── paddleocr_engine.py
│       │   │
│       │   ├── tts/
│       │   │   └── vieneu_engine.py
│       │   │
│       │   ├── persistence/
│       │   │   └── sqlite_job_repository.py
│       │   │
│       │   └── storage/
│       │       └── local_artifact_store.py
│       │
│       └── entrypoints/(Adapter đầu vào)
│           │
│           ├── cli.py
│           ├── worker.py
│           │
│           └── gui/
│               ├── app.py
│               │
│               ├── windows/
│               ├── widgets/
│               ├── viewmodels/
│               │
│               └── resources/
│                   ├── icons/
│                   └── styles/
│
├── tests/
│   │
│   ├── unit/
│   │   ├── domain/
│   │   └── application/
│   │
│   ├── integration/
│   │   └── adapters/
│   │
│   ├── e2e/
│   │
│   └── fixtures/
│
└── scripts/
```

## Ánh xạ từ Spring Boot sang Anan

| Spring Boot bạn quen | Anan |
|---|---|
| `controller/` | `entrypoints/` |
| `service/` | `application/use_cases/` |
| business orchestration | `application/pipeline/` |
| `entity/`, domain model | `domain/` |
| Repository interface | `application/ports/` |
| Repository implementation | `adapters/persistence/` |
| Feign/API client | `adapters/.../` |
| `@Configuration`, `@Bean` | `bootstrap.py` |
| `application.yml` | `config.py` / config file |
| implementation của interface | adapter |
| external SDK/library | nằm bên trong adapter |

## Quy tắc phụ thuộc cốt lõi

- Domain không phụ thuộc framework, UI hoặc provider cụ thể.
- Application điều phối use case và pipeline thông qua port.
- Adapter triển khai các port cho FFmpeg, ASR, OCR, TTS, persistence và external API.
- Entrypoint chỉ tiếp nhận tương tác và gọi application use case.
- `bootstrap.py` là composition root để ghép implementation cụ thể.
- Chỉ tạo folder khi đã có code thực tế thuộc về folder đó.

Chi tiết DAG và contract được tách sang [pipeline.md](pipeline.md).

