# DAG và hợp đồng các stage

> Đây là nguồn sự thật cho dependency, input/output contract, artifact revision, cache và retry/resume của pipeline V1.

Phần này hợp nhất thiết kế DAG, contract, artifact/cache/resume cho pipeline V1, bao gồm nguồn video dài. Các tên artifact là quy ước thiết kế, chưa phải file đã được tạo bởi một pipeline đang chạy.

Mục tiêu: URL hoặc video local → một final.mp4 tiếng Việt. Artifact trung gian chỉ dùng nội bộ. V1 dùng một voice Việt; VAD chỉ phát hiện vùng có lời nói. Speaker diarization và multi-speaker TTS là hướng phát triển tương lai, không thuộc DAG V1.

## Ánh xạ chức năng vào các stage
Giữ nguyên 14 stage trong cây thư mục. Không tạo thêm stage chỉ vì một công nghệ mới xuất hiện trong technical stack.
Một stage có thể chịu trách nhiệm cho nhiều bước xử lý liên quan nếu chúng cùng thuộc một mục tiêu nghiệp vụ của pipeline.

### `recognize_speech`
Chịu trách nhiệm tạo transcript tiếng Trung từ audio nguồn.
Bao gồm:
- VAD: xác định các khoảng thời gian có lời nói.
- Nếu cần trích các khoảng audio tương ứng để đưa vào ASR, adapter/hạ tầng audio thực hiện việc trích riêng và phải giữ được offset trên timeline gốc.
- VAD chỉ xác định vùng có lời nói, không tự thực hiện việc cắt audio.
- V1 chưa cần một VAD port độc lập.
- **ASR** nhận audio nguồn đã chuẩn bị và trả về transcript tiếng Trung cùng timestamp trên timeline nguồn.
- Kết quả từ các vùng VAD được chuẩn hóa và ghép thành transcript thống nhất.
- V1 không thực hiện hợp nhất transcript theo nhiều speaker.
ASR không mặc định sử dụng vocal stem từ source separation, vì separation có thể tạo artifact làm giảm chất lượng nhận diện.

### `separate_audio`
Chịu trách nhiệm tách audio nguồn thành các thành phần cần thiết cho bước mix sau này.
Trong V1:
- chạy trực tiếp từ audio nguồn;
- giữ lại background stem cho `mix_audio`;
- vocal stem không phải input mặc định của `recognize_speech`.
`recognize_speech` và `separate_audio` có thể hoạt động độc lập từ cùng một audio nguồn.

### `validate_pre_tts`
Chịu trách nhiệm kiểm tra và hiệu chỉnh dữ liệu trước khi sinh giọng Việt.
Ngoài việc kiểm tra bản dịch, stage này còn thực hiện **OCR có điều kiện** khi transcript nguồn có dấu hiệu đáng ngờ.
OCR được dùng để:
- đọc frame video tại đoạn cần xác minh;
- đối chiếu với transcript tiếng Trung;
- hỗ trợ xác nhận tên riêng, thuật ngữ hoặc nội dung ASR có confidence thấp.
OCR không trực tiếp chấm chất lượng bản dịch tiếng Việt.
Nếu OCR cung cấp đủ bằng chứng rằng source transcript sai:
1. hiệu chỉnh transcript nguồn;
2. cập nhật source đã được xác minh;
3. dịch lại phần bị ảnh hưởng;
4. tiếp tục validation trước TTS.

### `validate_post_tts`
Chịu trách nhiệm kiểm tra kết quả sau khi đã sinh audio TTS.
Nếu một segment lệch thời lượng lớn so với khoảng thời gian được phép, stage này có thể thực hiện vòng xử lý có giới hạn:
1. phát hiện segment lệch lớn;
2. rút gọn hoặc rewrite bản dịch;
3. TTS lại segment;
4. kiểm tra lại duration.
Kết quả cuối phải giữ **text và audio nhất quán**.
Không được để subtitle dùng một phiên bản text nhưng audio lại được sinh từ một phiên bản khác.

### `synchronize`
Chịu trách nhiệm đưa audio tiếng Việt vào đúng timeline của video.
Bao gồm:
- trim silence;
- pad silence;
- time-stretch trong giới hạn cho phép;
- đặt từng segment vào đúng vị trí trên timeline nguồn;
- assembly các segment thành timeline audio hoàn chỉnh.
Stage này không quyết định rewrite nội dung. Nếu lệch quá lớn để sync hợp lý, việc rewrite và TTS lại thuộc `validate_post_tts`.

### `mix_audio`
Chịu trách nhiệm tạo audio mix cuối.
Bao gồm:
- trộn giọng Việt với background stem;
- ducking nếu cấu hình bật;
- cân bằng mức âm lượng;
- loudness control cho output cuối.

### `build_subtitles`
Chịu trách nhiệm tạo phụ đề khi user bật subtitle.
Phụ đề phải sử dụng:
- phiên bản text cuối cùng sau toàn bộ rewrite/TTS lại;
- timing cuối sau `synchronize`.
Không lấy trực tiếp bản dịch ban đầu nếu text đã bị thay đổi trong `validate_post_tts`.

### `render_video`
Chịu trách nhiệm tạo file video ứng viên cuối cùng.
Bao gồm:
- encode/mux video và audio;
- burn subtitle nếu cấu hình yêu cầu;
- watermark nếu bật;
- kết hợp các xử lý hình ảnh trong cùng một lần encode khi có thể để tránh encode video thừa;
- verify file output.
Finalization phải theo hướng atomic:
`temporary output → verify → final.mp4`
Chỉ sau khi file ứng viên vượt qua verify mới được công bố thành `final.mp4`.

### `cleanup`
Chỉ chạy sau khi đã có `final.mp4` hợp lệ.
Chịu trách nhiệm:
- xóa các temp artifact lớn thuộc job;
- giải phóng working data không còn cần thiết.
Không được xóa:
- video local gốc do user cung cấp;
- source media hoàn chỉnh đã tải từ URL và được giữ theo policy cache/resume của Anan.
Nếu job thất bại, cleanup phải tuân theo failed-job cache policy để vẫn có thể retry/resume khi cần.

### VAD và nguồn audio cho ASR
prepare_audio tạo các working audio phù hợp với từng tác vụ từ cùng nguồn, kèm thông tin quy đổi về timeline video. ASR không bắt buộc dùng đúng sample rate hoặc số kênh của bản audio dành cho separation.
ASR nhận source_audio_for_asr, chưa qua source separation. separate_audio nhận source_audio_for_separation. Hai nhánh độc lập về dependency. Việc cả hai đã sẵn sàng không đồng nghĩa được chạy GPU đồng thời.
VAD là bước con của recognize_speech: nhận audio và trả các khoảng thời gian có lời nói, ví dụ từ giây 10 đến giây 14. VAD không tự cắt hoặc chỉnh sửa âm thanh. Nếu ASR cần từng đoạn riêng, code xử lý audio trong adapter/hạ tầng mới trích các đoạn theo mốc VAD và giữ mapping về timeline nguồn. VAD không có trạng thái stage độc lập trong bản đề xuất này; phiên bản model và cấu hình VAD vẫn tham gia cache key của stage nhận diện.
### OCR và source correction
Chế độ mặc định là SMART: kích hoạt khi có dấu hiệu transcript đáng ngờ, tên riêng/thuật ngữ cần xác minh hoặc validator yêu cầu. OFF không gọi OCR; việc quét rộng hơn chỉ thực hiện khi người dùng chủ động chọn chế độ tương ứng, không phải mặc định V1.
validate_pre_tts nhận các cờ nghi ngờ từ ASR và tự kiểm tra source consistency. Khi cần, stage lấy frame từ video nguồn, gọi OCR và đối chiếu bằng chứng. Kết quả OCR cũng có thể sai; không tự động coi mọi chữ OCR đọc được là đáp án đúng.
Nếu cần sửa transcript nguồn (text tiếng Trung): tạo revision mới cho bộ text đã hiệu chỉnh → dịch lại segment và phần ngữ cảnh bị ảnh hưởng → chạy lại pre-TTS validation. Việc này không thay video nguồn của job. Vòng sửa có giới hạn; stage chỉ hoàn tất khi có bộ transcript nguồn và bản dịch nhất quán. Không sửa đè các artifact đã commit của recognize_speech hoặc translate.

## DAG cấp stage
Danh sách bên phải là các stage cần hoàn thành trước. Khai báo rõ các producer mà stage tiêu thụ dữ liệu trực tiếp, kể cả khi đã có quan hệ phụ thuộc gián tiếp.
```python
DEPENDENCIES = {
    "ingest": [],
    "inspect_media": ["ingest"],
    "prepare_audio": ["inspect_media"],
    "recognize_speech": ["prepare_audio"],
    "separate_audio": ["prepare_audio"],
    "translate": ["recognize_speech"],
    "validate_pre_tts": [
        "translate", "recognize_speech", "inspect_media"
    ],
    "synthesize_speech": ["validate_pre_tts"],
    "validate_post_tts": ["synthesize_speech", "validate_pre_tts"],
    "synchronize": ["validate_post_tts", "inspect_media"],
    "mix_audio": ["synchronize", "separate_audio"],
    "build_subtitles": ["validate_post_tts", "synchronize"],
    "render_video": ["inspect_media", "mix_audio", "build_subtitles"],
    "cleanup": ["render_video"],
}
```
Hai vòng sửa trong validation không được biểu diễn bằng cạnh quay ngược trong DAG. 
Stage gọi lại các capability cần thiết qua port và tạo output revision của chính mình. 
Retry/resume ở cấp engine là một lần thực thi mới trên cùng cấu trúc dependency.
Nếu phụ đề tắt, build_subtitles ghi kết quả rõ ràng enabled=false và trạng thái SKIPPED. render_video chấp nhận đúng trường hợp skip do cấu hình này. 
Không coi mọi SKIPPED, FAILED hoặc CANCELLED là dependency đã đáp ứng. 
Khi phụ đề bật, phải có artifact phụ đề hợp lệ.

## Quy ước contract, cache và retry dùng chung
### Phạm vi thao tác của người dùng
Mỗi job gắn với nguồn và cấu hình đã tiếp nhận. GUI cung cấp Run, Hủy và Thử lại khi lỗi. Người dùng không chọn artifact, thay nguồn trong job cũ, sửa dependency hoặc chọn từng stage để phục hồi. Muốn xử lý video khác hoặc đổi cấu hình do người dùng lựa chọn thì tạo job mới.
Khi bấm Thử lại, Anan dùng các đầu vào đã chuẩn bị còn hợp lệ để chạy lại bước lỗi rồi tự tiếp tục pipeline. Việc kiểm tra, giữ kết quả và khôi phục artifact là trách nhiệm nội bộ. Nếu không còn đầu vào hợp lệ để khôi phục, báo rõ bước lỗi và lý do: không thể tiếp tục job này, cần chạy lại từ đầu. Không yêu cầu người dùng tự sửa cache.
### Contract và định danh artifact
- Media nội bộ được quản lý bằng artifact_id và revision. artifact_id nhận diện một artifact logic, còn revision nhận diện một lần tạo cụ thể của artifact đó. Cặp này phải duy nhất trong registry artifact; nếu ID chỉ duy nhất trong một job thì tham chiếu phải kèm job_id.
- Mỗi bản output được tạo mới có revision mới, kể cả chạy lại cùng input/cấu hình hoặc tạo ra nội dung giống lần trước. Revision được cấp và lưu bền vững, không tái sử dụng; không phải timestamp, mtime hay phiên bản code/model. Cache hit chỉ tái sử dụng revision đã commit, không tạo ra revision giả. Nếu một manifest tham chiếu lại audio đã có mà không sinh audio mới thì giữ nguyên revision của audio đó.
- Output được ghi trong vùng attempt riêng, đóng/hoàn tất ghi, kiểm tra theo contract rồi mới commit. Payload và hồ sơ của revision đã commit không được sửa đè; cần tạo kết quả mới thì cấp revision mới. Registry có thể cập nhật con trỏ revision đang được chọn hoặc đánh dấu revision không còn dùng được, nhưng không sửa hồ sơ cũ để hợp thức hóa file bị đổi.
- Không bắt buộc content hash cho toàn bộ audio/video lớn. Không đọc lại toàn bộ media chỉ để tạo/kiểm tra cache key khi resume/retry. Transcript, bản dịch, prompt, cấu hình và dữ liệu nhỏ khác vẫn có thể dùng content hash.
- Manifest, transcript hoặc dub plan tham chiếu media phải ghi đúng (artifact_id, revision) cần dùng; không tra “file mới nhất” theo cùng tên. Các basename như background.wav trong phần 4 là tên logic; file thực tế thuộc đường dẫn attempt/revision riêng.
- Segment tối thiểu có segment_id, start, end, text_zh; thêm text_vi sau dịch. Mốc thời gian dùng giây trên timeline video nguồn, thỏa 0 <= start < end <= video_duration. Giữ segment_id khi chỉ sửa text; nếu thực sự chia/gộp segment phải tạo mapping revision rõ ràng.
- Không mặc định mọi model ASR đều có timestamp/confidence giống nhau. Adapter phải chuẩn hóa timestamp theo contract, có thể sử dụng vùng VAD; confidence không được bịa nếu provider không trả về.
- VAD chỉ phát hiện vùng lời nói. Nếu cần trích/cắt audio theo các vùng đó, thành phần xử lý audio thực hiện riêng và lưu offset/mapping gốc. Không ghép các đoạn speech thành timeline mới rồi dùng trực tiếp timestamp đó cho video nguồn.
- Transcript rỗng chỉ hợp lệ khi xác nhận không có lời nói. Khi đó dùng danh sách segment rỗng, voice timeline im lặng và không gọi dịch/TTS cho segment không tồn tại. Media thiếu audio stream hoặc không giải mã được được báo lỗi ở bước kiểm tra/chuẩn bị.

### Manifest và kiểm tra metadata nhanh
Mỗi file artifact cần được sử dụng lại phải có hồ sơ mô tả đủ thông tin để Anan xác định đúng artifact, kiểm tra tính hợp lệ và quyết định có thể reuse hay không.
Manifest của một artifact cần có các thông tin sau:
### Định danh artifact
artifact_id
revision
Dùng để xác định chính xác artifact và revision đang được tham chiếu.
Không được chỉ dựa vào tên file để xác định một artifact.

### Loại và contract
artifact_type
schema_version
Cho biết artifact chứa loại dữ liệu gì và phải được đọc theo schema/contract nào.
Giúp phát hiện trường hợp artifact cũ không còn tương thích với code hiện tại.

### Vị trí và ownership
path / reference
ownership
Dùng để:
- tìm file thực tế;
- xác định file thuộc job hay thuộc nguồn bên ngoài;
- quyết định file có được phép cleanup hay không.
Ví dụ, working artifact do Anan tạo có thể được cleanup, trong khi video local gốc của user thì không.

### Trạng thái commit
Manifest phải cho biết artifact đã được commit hoàn chỉnh hay vẫn chỉ là output tạm của một attempt.
TEMP / UNCOMMITTED
COMMITTED
Trạng thái commit của artifact độc lập với trạng thái của stage.
Một stage từng `RUNNING`, `FAILED` hoặc bị gián đoạn có thể để lại file trên disk, nhưng những file chưa được commit không được coi là output hợp lệ để downstream reuse.

### Metadata file để kiểm tra nhanh
Lưu ít nhất:
size_bytes
mtime
Trong đó:
`size_bytes` là kích thước file được ghi nhận khi artifact được tiếp nhận hoặc commit.
`mtime` là thời điểm file được sửa đổi, lưu với độ chính xác cao nhất mà filesystem/API thực tế cung cấp, ví dụ `mtime_ns`.
Không được giả định rằng filesystem thực sự có độ phân giải thời gian đến nano giây chỉ vì API trả giá trị dưới dạng nanosecond.
Các metadata này cho phép Anan thực hiện kiểm tra nhanh trước khi quyết định có cần kiểm tra sâu hơn hay không.

### Provenance — nguồn gốc kết quả
Manifest phải lưu đủ thông tin để biết artifact được tạo ra từ đâu và bằng cách nào.
Bao gồm những thông tin liên quan như:
job_id
producer stage
producer attempt
input artifact/revision
relevant configuration
contract/code version
provider/model/tool thực tế

Ví dụ, transcript cần có khả năng truy ngược về:
audio revision
+ ASR model
+ VAD model/config
+ recognize_speech attempt
→ transcript revision
Provenance phục vụ cache validation, retry/resume và debug khi kết quả có vấn đề.

### Content hash
Có thể lưu:
content_hash
khi:
- artifact nhỏ;
- hash đã có sẵn từ quá trình ingest;
- hoặc hash được tạo tự nhiên trong quá trình xử lý.
Không bắt buộc đọc lại toàn bộ media lớn chỉ để tính hash.
Với video/audio dài, ưu tiên metadata và provenance có sẵn để kiểm tra nhanh, chỉ hash khi thực sự cần theo policy.

### Manifest cho output gồm nhiều file
Nếu output của một stage gồm nhiều artifact, cần có manifest tập hợp mô tả chính xác những thành phần thuộc output đó.
Ví dụ:
recognize_speech output
│
├── transcript revision 3
├── segment data revision 2
└── manifest

Manifest tập hợp phải tham chiếu chính xác:
artifact_id + revision
của từng thành phần.
Không được hiểu đơn giản là:
"lấy các file hiện có trong folder"
vì folder có thể chứa artifact từ attempt hoặc revision cũ.
Nhờ đó downstream luôn biết chính xác **bộ output nào đã được commit và những revision nào cấu thành bộ output đó**.

Ghi nhận kích thước và mtime sau khi file đã ghi xong và ở vị trí ổn định dùng cho commit. Việc commit phải nhất quán giữa file, manifest và state; chỉ báo stage thành công khi bộ output bắt buộc đã commit đầy đủ. Không lấy mtime làm revision hoặc bằng chứng độc lập về nội dung.
Khi định tái sử dụng artifact, kiểm tra đúng những artifact mà thao tác tiếp theo cần đọc:
1. Manifest đúng loại/schema và đúng revision đã commit; stage cache record khớp K và trỏ tới revision đó.
2. File tại vị trí đã ghi vẫn tồn tại.
3. Kích thước và mtime hiện tại khớp hồ sơ.
4. Với dữ liệu nhỏ có content hash, có thể đọc và đối chiếu hash/schema. Với media lớn, không bắt buộc mở/đọc toàn bộ file để xác minh content hash.
Tra registry/manifest theo ID và chỉ kiểm tra các file cần dùng. Không quét/hash toàn bộ thư mục job mỗi lần resume, không lần lượt đọc lại mọi artifact của các nhánh hoặc tổ tiên không cần cho lần thực thi hiện tại. Các tham chiếu revision có thể được tra từ hồ sơ mà không đọc payload media.
### Cache key chung — ký hiệu K
```text
K = hash(
    stage_id,
    contract_version,
    stage_implementation_version,
    input_artifact_references,       # các (artifact_id, revision) đã chốt
    small_data_content_hashes,       # transcript/text/context/config... nếu dùng
    relevant_configuration,
    effective_provider_model_and_tool_versions
)
```
hash(...) ở đây hash bản mô tả nhỏ, được chuẩn hóa theo thứ tự ổn định; không có nghĩa đọc và hash các byte của mọi file media. Đối với media nội bộ, danh tính revision đầu vào là thành phần bắt buộc trong K. Khi revision một input trực tiếp thay đổi, K của stage tiêu thụ nó thay đổi. Khi stage đó tạo output mới, revision mới tiếp tục được truyền tới các bước phụ thuộc.
K nhận diện yêu cầu xử lý để tra cache; revision nhận diện một bản output đã được tạo. Hai lần thực thi có cùng K vẫn tạo revision output khác nhau nếu thật sự sinh lại kết quả. Cache record gắn K với bộ revision output đã commit, không đồng nhất hai khái niệm này.
Chỉ đưa cấu hình thực sự ảnh hưởng vào key. Không đưa API key, cookie, token vào metadata/log. Với model/tool/voice asset, dùng định danh và phiên bản đã ghi nhận; hash model đã pin có thể là một định danh sẵn có, không phải yêu cầu đọc lại file trọng số trong mỗi lần kiểm tra cache. Các cache key ở phần 4 đều áp dụng quy ước chung này.
Một key trùng không đảm bảo lần sinh AI mới cho kết quả giống tuyệt đối; cache dùng lại kết quả đã commit còn hợp lệ. Nếu chuyển sang recognizer dự phòng theo policy, cache/provenance phải phản ánh provider/model thực tế, không ghi kết quả dự phòng dưới danh tính model chính.
### Nguồn bên ngoài và phạm vi bảo đảm
Nguồn URL/local phải được xác nhận khi tiếp nhận: đúng nguồn người dùng chọn, đọc/truy cập được, không phải bản tải dở; ghi nhận định dạng/thông tin nguồn và metadata sẵn có. URL cần thông tin nguồn/biến thể tải đã thực sự nhận, cùng xác nhận hoàn tất của downloader; local cần hồ sơ file thực tế khi tiếp nhận. Không dùng riêng URL, tên file hoặc đường dẫn làm bằng chứng nội dung không đổi.
Một bản tải hoàn chỉnh do Anan quản lý được commit thành media nội bộ và được đánh dấu protected_input, không thuộc tập auto-cleanup. Nếu dùng local trực tiếp thay vì sao chép, manifest phải ghi đây là tham chiếu bên ngoài, ownership thuộc người dùng và metadata lúc tiếp nhận. ID/revision nhận diện hồ sơ nguồn đã nhận, không khiến file bên ngoài trở thành bất biến. Anan kiểm tra metadata của tham chiếu này khi cần dùng; nếu mất hoặc không khớp thì không tự nhận file hiện tại làm nguồn thay thế trong job cũ. Việc giữ bản riêng hay tham chiếu read-only là chi tiết nội bộ, không thêm tùy chọn sửa nguồn trong GUI.
Phạm vi bảo đảm: cơ chế revision + commit + metadata là chính sách tin cậy artifact nội bộ do Anan quản lý. Kích thước và mtime không chứng minh toàn bộ nội dung còn nguyên vẹn; chấp nhận không phát hiện mọi sửa đổi/hỏng dữ liệu mà metadata vẫn giữ nguyên. Không có yêu cầu full-content verification mặc định trên media lớn mỗi lần resume/retry.
Kiểm tra metadata phục vụ cache không thay thế việc validate output lúc tạo/commit hoặc việc đọc media để thực hiện xử lý/verify theo contract. Nếu một lần xử lý thực tế phát hiện file hỏng dù metadata còn khớp, xử lý như artifact không hợp lệ.
### Policy lỗi chung — ký hiệu B
- Input/schema/cấu hình không hợp lệ, thiếu model hoặc thiếu credential: FAILED với nguyên nhân rõ; không lặp lại cùng yêu cầu vô ích.
- Lỗi tạm thời như timeout/kết nối gián đoạn/lỗi dịch vụ có thể phục hồi: retry có backoff trong giới hạn hữu hạn max_stage_retries được validate từ cấu hình.
- File cần dùng bị mất, metadata không khớp hoặc xử lý thực tế phát hiện hỏng: không dùng artifact, chuyển sang quy tắc khôi phục/invalidation bên dưới. Không cập nhật size/mtime trong hồ sơ cũ để làm cho file có vẻ hợp lệ.
- Lỗi tài nguyên phải theo resource policy; không liên tục chạy lại khi biết GPU vẫn thiếu bộ nhớ. Mặc định chỉ một GPU-heavy workload tại một thời điểm.
- Lỗi chất lượng chỉ tự sửa ở stage có vòng sửa quy định. Ngân sách sửa nội dung tách biệt với retry do lỗi kỹ thuật.
- Cancel dừng ở điểm an toàn, không bắt đầu việc mới hoặc công bố output dở; cleanup theo policy job.
- Error/log có job_id, stage_id, attempt, segment_id nếu liên quan. GUI hiển thị lý do dễ hiểu và thao tác Thử lại nếu khả thi; không buộc người dùng đọc manifest hoặc chọn stage/artifact.
- Chỉ đánh dấu SUCCESS khi output bắt buộc đã validate và commit. Trạng thái SUCCESS cũ không tự chứng minh file vẫn dùng được.
### Resume, khôi phục và invalidation
1. Khi Thử lại, engine kiểm tra cache record, manifest và metadata của những artifact cần cho bước sắp chạy. Giữ các revision đã commit còn hợp lệ; không tạo lại chỉ vì ứng dụng đã khởi động lại.
2. Nếu file mất/metadata lệch/hỏng, loại revision đó khỏi tập có thể sử dụng, ghi rõ lý do, đánh dấu producer cần khôi phục/chạy lại và các downstream phụ thuộc cần kiểm tra lại. Không xóa hoặc chạy lại các nhánh độc lập còn hợp lệ.
3. Nếu producer có thể tạo lại kết quả từ các input revision cũ còn hợp lệ, engine tự lập kế hoạch khôi phục tối thiểu, tạo attempt và output revision mới. Người dùng vẫn chỉ bấm Thử lại; không được yêu cầu chọn artifact hoặc sửa DAG. Với artifact cũ không hợp lệ, không được chọn lại chính cache record cũ làm kết quả khôi phục.
4. Nếu không còn đầu vào hợp lệ để khôi phục — ví dụ nguồn cần thiết bị mất/thay đổi và không có bản nguồn đã giữ — dừng và báo không thể tiếp tục job này, cần chạy lại từ đầu. Không tự thay nguồn, không trộn kết quả nguồn mới với transcript cũ và không bắt người dùng sửa cache. Việc đánh dấu cần khôi phục không đồng nghĩa luôn khôi phục được.
5. Khi có output revision mới, downstream phải dùng đúng revision mới để tính K; cache gắn với revision cũ không được nhận là khớp. Có thể invalidation toàn bộ descendants trước; chỉ tối ưu theo segment khi có contract/cache đủ rõ.
Retry bước lỗi không tự chạy lại mọi bước trước nó. Output revision cũ không được ghép với text/audio revision mới. Nếu lỗi chỉ ở cleanup và final.mp4 đã commit còn hợp lệ, retry cleanup; không tái tạo các temp không còn cần thiết. Job đã thành công và dọn temp không phải một giao diện sửa/chạy lại từng stage: nhu cầu xử lý mới tạo job mới.

## Hợp đồng của 14 stage
### 01. `ingest`
- depends_on: không có.
- input contract: URL nguồn hoặc đường dẫn video local, cấu hình tải và workspace đã gắn với job khi bấm Run. Trong job cũ, GUI không cho thay nguồn, chọn artifact hoặc sửa dependency; nguồn/cấu hình mới tạo job mới. File local gốc thuộc người dùng, không phải temp được phép xóa. Source media hoàn chỉnh tải từ URL cũng là input được bảo vệ khỏi auto-cleanup.
- output artifacts: source_media và source_manifest.json: nguồn đã được tiếp nhận, (artifact_id, revision), loại nguồn, đường dẫn, ownership, trạng thái commit, size/mtime và provenance/thông tin tải khi có. Media nội bộ đã commit không sửa đè; local dùng trực tiếp phải được đánh dấu là tham chiếu bên ngoài với hồ sơ lúc tiếp nhận. Không bắt buộc content hash toàn bộ video nguồn.
- cache key: Bước này chưa có media input nội bộ trước khi tiếp nhận. Khóa tra cứu ban đầu dựa trên nguồn/cấu hình đã chốt của job, contract/code và downloader/tool version; hồ sơ nguồn thực tế cùng metadata được xác nhận ở lần nhận đầu tiên. Chỉ tái sử dụng đúng source revision đã commit của job khi manifest và size/mtime còn khớp; không suy luận chỉ từ URL/tên file, không hash lại toàn bộ video. Sau tiếp nhận, các stage sau đưa tham chiếu source (artifact_id, revision) vào K.
- failure/retry policy: B. Thử lại dùng đầu vào/trạng thái tải đã được job ghi nhận. Download chưa commit chỉ được tải tiếp nếu adapter hỗ trợ, phần tạm và thông tin nguồn còn hợp lệ; nếu không thì tải lại trong phạm vi yêu cầu ingest chưa hoàn thành. Không công bố file tải dở. Nguồn đã commit mà mất/metadata lệch thì không âm thầm chấp nhận một bản tải/file khác làm cùng revision. Engine chỉ khôi phục khi còn nguồn đã tiếp nhận hợp lệ; nếu không, báo lý do và yêu cầu chạy lại từ đầu. GUI chỉ có thông báo và Thử lại khi khả thi, không có chọn file thay thế hay quản lý từng stage.
### 02. `inspect_media`
- depends_on: ingest.
- input contract: Source media đã được ingest xác nhận, đúng (artifact_id, revision), cùng manifest và metadata nhanh còn hợp lệ theo mục 3; đọc media phục vụ probe khi stage thực sự cần chạy.
- output artifacts: media_info.json: source (artifact_id, revision), video/audio streams được chọn, duration, codec, sample rate, channels, time base/start offset và thông tin quy đổi timeline. Đây là artifact dữ liệu nhỏ, có revision và có thể có content hash. Không encode video trong inspection.
- cache key: K với source (artifact_id, revision), quy tắc chọn stream, cấu hình probe và phiên bản FFprobe; source được kiểm tra nhanh theo manifest/metadata, không dựa vào hash toàn bộ video.
- failure/retry policy: B. File hỏng, không có video hoặc không có audio stream phù hợp thì fail có lý do. Không lặp probe vô hạn trên cùng file không hợp lệ.
### 03. `prepare_audio`
- depends_on: inspect_media.
- input contract: source media qua tham chiếu trong media info, audio stream đã chọn và cấu hình working audio của các adapter.
- output artifacts: source_audio_for_asr, source_audio_for_separation và audio_assets.json: tham chiếu (artifact_id, revision) của từng audio, định dạng, sample rate/channels, duration, commit status, size/mtime và mapping về timeline video. Có thể cùng tham chiếu một revision nếu hai contract tương thích; không bắt buộc hash media.
- cache key: K với source media (artifact_id, revision), revision của media info/stream đã chọn, cấu hình extract/resample/channel conversion/timeline và phiên bản FFmpeg.
- failure/retry policy: B. Kiểm tra output đọc được và timeline đúng trước khi commit; retry thay thế attempt dở. Không tự cắt bỏ các khoảng im lặng theo cách làm dịch timeline video.
### 04. `recognize_speech`
- depends_on: prepare_audio; không phụ thuộc separate_audio.
- input contract: source_audio_for_asr chưa qua separation, metadata audio, mapping timeline và cấu hình VAD/ASR/ngôn ngữ tiếng Trung.
- output artifacts: speech_regions.json, transcript_raw.json: vùng lời nói do VAD xác định, segment ID, thời gian trên timeline nguồn, text tiếng Trung, confidence/cờ nghi ngờ nếu có và provenance. Nếu cần cắt/trích audio, thành phần xử lý audio thực hiện riêng theo các vùng VAD và giữ offset. Các JSON có revision và có thể dùng content hash.
- cache key: K với (artifact_id, revision) của source_audio_for_asr, revision/hash dữ liệu mapping nhỏ, định danh/version model VAD + ASR đã ghi nhận, cấu hình segmentation/language/inference và provider thực tế. Không hash lại toàn bộ audio hoặc trọng số model để kiểm tra cache.
- failure/retry policy: B. Confidence thấp tạo cờ cần xác minh, không tự coi là lỗi kỹ thuật. Không có speech có thể trả transcript rỗng; có speech nhưng nhận diện rỗng hoặc timestamp sai thì phải xử lý/báo lỗi. Fallback sang recognizer khác chỉ theo cấu hình rõ ràng và có provenance riêng.
### 05. `separate_audio`
- depends_on: prepare_audio.
- input contract: source_audio_for_separation từ audio nguồn và cấu hình separation. Đặc tả này mô tả đường chạy mặc định bật separation của V1.
- output artifacts: background.wav và separation_manifest.json, ghi (artifact_id, revision), duration, offset, commit status, size/mtime và provenance của background. Vocal stem có thể là artifact nội bộ riêng nếu cần; mỗi output mới có revision mới, không bắt buộc content hash media.
- cache key: K với (artifact_id, revision) của source_audio_for_separation, định danh/version model separator đã ghi nhận và cấu hình inference/channel/sample rate liên quan.
- failure/retry policy: B. Kiểm tra stem đọc được và khớp timeline. Nếu tách thất bại thì fail stage; không âm thầm dùng nguyên audio tiếng Trung làm background.
### 06. `translate`
- depends_on: recognize_speech.
- input contract: transcript tiếng Trung, segment IDs/timing, ngữ cảnh cần dịch, glossary và cấu hình ngôn ngữ Trung → Việt.
- output artifacts: translation_draft.json: bản dịch Việt gắn với segment ID/source revision, kèm context/glossary revision và provider provenance. Đây là bản nháp trước validation.
- cache key: K với các revision input liên quan và content hash dữ liệu nhỏ của transcript/ngữ cảnh/glossary thực sự sử dụng nếu áp dụng, provider/model, prompt/schema version và tham số sinh nội dung. Cache theo nhóm segment phải tính cả ngữ cảnh mà nhóm đó đã đọc; không đọc lại audio/video để tính key dịch.
- failure/retry policy: B. Kiểm tra structured output, thiếu/thừa/trùng segment và kiểu dữ liệu. Output sai cấu trúc chỉ được yêu cầu sửa trong ngân sách hữu hạn; hết giới hạn thì fail, không chuyển bản dịch thiếu sang TTS.
### 07. `validate_pre_tts`
- depends_on: translate, recognize_speech, inspect_media.
- input contract: transcript nguồn và cờ nghi ngờ, bản dịch nháp, video nguồn qua media reference, glossary/context, validation policy và OCR mode. OCR đọc frame video, không đọc audio.
- output artifacts: segments_validated.json: bộ transcript nguồn/text Việt đã thống nhất để TTS sử dụng; pre_tts_report.json; OCR evidence/repair history khi có. Transcript đã sửa được ghi thành revision mới của bộ validated, giữ liên kết về transcript gốc; không thay video nguồn.
- cache key: K với các revision transcript/bản dịch/context/glossary, content hash dữ liệu nhỏ nếu dùng, source video (artifact_id, revision) phục vụ OCR và chính sách chọn frame/crop, OCR mode/model/config, validator/rule/prompt version, cấu hình ước lượng thời lượng và các provider kiểm tra/sửa. Source video chỉ kiểm tra metadata khi dùng cache; trích frame khi stage thật sự chạy OCR.
- failure/retry policy: B. Rule validation trước, LLM khi cần; targeted OCR xác minh source đáng ngờ. Sửa source thì dịch lại phần bị ảnh hưởng; chỉ sửa tiếng Việt thì kiểm tra lại ngữ nghĩa/độ tự nhiên/độ dài. Các vòng này có giới hạn; lỗi bắt buộc chưa giải quyết thì fail, không coi OCR thiếu bằng chứng là source đã được xác minh.
### 08. `synthesize_speech`
- depends_on: validate_pre_tts.
- input contract: các segment đã qua pre-TTS validation, text Việt và một voice đã cấu hình cho V1. TTSEngine chỉ synthesize; không bắt buộc nhận target_duration và không chịu trách nhiệm fit timeline.
- output artifacts: WAV theo segment trong các vùng attempt/revision của tts_initial/, cùng tts_initial_manifest.json: segment ID, (artifact_id, revision) audio, text/voice/model provenance, commit status, size/mtime, định dạng và duration. Audio được tạo lại có revision mới dù text và cấu hình giữ nguyên.
- cache key: K theo input revision/text từng segment, content hash text nhỏ nếu dùng, voice identity/version hoặc (artifact_id, revision) của voice asset nội bộ, model/version và cấu hình pronunciation/inference/output. Không bắt buộc hash toàn bộ voice media. Cache từng segment chỉ dùng khi input độc lập; model nhận context thì context cũng vào key.
- failure/retry policy: B. Lỗi một segment có thể retry/reuse riêng nếu manifest cho phép; giữ audio hợp lệ của segment khác. File không đọc được hoặc trống bất thường không được commit. Lệch thời lượng chuyển cho post-TTS validation xử lý, không tự stretch trong adapter TTS.
### 09. `validate_post_tts`
- depends_on: synthesize_speech, validate_pre_tts.
- input contract: text/source/timing đã validated, audio TTS thực tế, sync policy, cấu hình voice/TTS và các cấu hình dịch/validation cần cho vòng rewrite.
- output artifacts: dub_final.json, post_tts_report.json và manifest tham chiếu đúng (artifact_id, revision) của audio cuối. Mỗi segment có text Việt cuối, duration và kế hoạch sync. Audio được dùng lại giữ revision cũ; audio sinh lại trong vòng sửa có revision mới. Không sửa đè audio/manifest TTS đã commit.
- cache key: K với revision và content hash dữ liệu text/source nhỏ nếu dùng, các (artifact_id, revision) audio TTS cùng duration đã ghi trong manifest, voice/TTS config, ngưỡng silence/timing/stretch, prompt/model/glossary/context dùng khi rewrite, validation policy và giới hạn vòng sửa. Cache hit không đo/đọc lại toàn bộ audio chỉ để xác minh key.
- failure/retry policy: B. Khi stage thực sự chạy, đo duration, silence và khả năng fit timeline. Lệch nhỏ/vừa thì lập kế hoạch trim/pad/stretch; lệch lớn thì rewrite → kiểm tra pre-TTS liên quan → TTS lại → đo lại, theo segment và có giới hạn. Không cho bản rút gọn sai nghĩa đi tiếp. Nếu cần sửa source, ghi lỗi có nguyên nhân để engine lập kế hoạch source validation/invalidation nội bộ khi khả thi; không yêu cầu người dùng tự chọn stage và không thay video nguồn trong job cũ.
### 10. `synchronize`
- depends_on: validate_post_tts, inspect_media.
- input contract: dub plan/text/audio cuối, kế hoạch sync được chấp nhận, video duration/timeline và policy xử lý khoảng im lặng/overlap.
- output artifacts: Các audio sau sync và voice_timeline.wav có (artifact_id, revision) riêng, cùng timing_final.json/manifest ghi text/audio revision, vị trí segment, commit status, size/mtime. Timeline giữ đúng vị trí trên video nguồn; bản audio đã commit không bị ghi đè khi retry.
- cache key: K với các (artifact_id, revision) audio cuối, revision/hash của dub plan và timing nhỏ nếu dùng, media info revision/target duration, trim/pad/stretch/overlap policy, output audio config và phiên bản FFmpeg.
- failure/retry policy: B. Kiểm tra timing sau xử lý, giới hạn stretch, clipping và overlap theo policy. Không xếp nối các câu làm trôi timeline. Không fit được thì báo lỗi gắn với segment để engine xử lý trong giới hạn policy hoặc dừng có lý do; không bắt người dùng chỉnh từng segment/stage, không stretch quá giới hạn hoặc cắt mất lời để báo thành công.
### 11. `mix_audio`
- depends_on: synchronize, separate_audio.
- input contract: voice timeline Việt và background stem cùng mapping/duration, cấu hình gain/ducking/loudness và output audio.
- output artifacts: mixed_audio.wav có (artifact_id, revision) và metadata commit/size/mtime; mix_report.json ghi duration, kết quả kiểm tra mức âm/clipping và loudness áp dụng. Input provenance ghi rõ revision voice timeline và background đã dùng.
- cache key: K với (artifact_id, revision) của voice timeline và background, timing/mix/gain/ducking/loudness/output config cùng phiên bản FFmpeg; không hash toàn bộ hai audio để kiểm tra cache.
- failure/retry policy: B. Kiểm tra audio đầu ra và độ khớp timeline trước khi commit. Background thiếu/hỏng hoặc mix không đạt policy thì fail stage; không bỏ giọng Việt hoặc đưa lại lời thoại nguồn để che lỗi.
### 12. `build_subtitles`
- depends_on: validate_post_tts, synchronize.
- input contract: text Việt cuối từ dub_final.json, timing cuối và cấu hình bật/tắt, font/style/layout subtitle. Không đọc bản dịch nháp trước rewrite để tạo sub.
- output artifacts: subtitles.ass và subtitle_manifest.json nếu bật; nếu tắt chỉ có manifest enabled=false, không yêu cầu file ASS.
- cache key: K với các revision text/timing cuối, content hash dữ liệu nhỏ nếu dùng, enabled flag, style/config và font identity/version hoặc hash font nhỏ đã ghi nhận, cùng phiên bản công cụ sinh subtitle.
- failure/retry policy: B. Tắt thì SKIPPED có lý do và manifest rõ. Bật nhưng thiếu font/cấu hình không hợp lệ/timing sai thì fail, không âm thầm bỏ subtitle. Phụ thuộc style chỉ liên quan subtitle và downstream; đây là phạm vi kỹ thuật, không cung cấp chức năng đổi style rồi chạy lại từng stage trong job cũ ở GUI V1.
### 13. `render_video`
- depends_on: inspect_media, mix_audio, build_subtitles.
- input contract: source video reference, mixed audio đã kiểm tra, subtitle result hợp lệ theo enabled flag, watermark asset/config nếu bật, encode/mux/verify settings và output destination.
- output artifacts: Mỗi attempt có file ứng viên final.tmp.mp4 riêng, verify_report.json và finalization receipt. Candidate được kiểm tra rồi atomic publish thành final.mp4; receipt/manifest ghi (artifact_id, revision), commit status, vị trí cuối, size/mtime và provenance. Không sửa đè bytes của revision đã commit; file tạm không là output hoàn chỉnh.
- cache key: K với source video và mixed audio (artifact_id, revision), subtitle result revision/hash dữ liệu nhỏ nếu dùng, font identity/version, watermark asset revision hoặc hash asset nhỏ, vị trí/style, encode/mux/verify config và phiên bản FFmpeg/FFprobe. Resume kiểm tra destination, receipt, commit status và size/mtime của file cần dùng; không hash lại toàn bộ source/mixed audio/final video.
- failure/retry policy: B. Kết hợp burn-in/watermark trong lần encode cần thiết; stream copy khi phù hợp. Validate candidate theo verify policy khi tạo kết quả, trước publish; việc này tách biệt với kiểm tra metadata nhanh khi resume. Candidate và final cùng filesystem để atomic rename. Lỗi verify không công bố file hỏng; lỗi publish có thể tiếp tục từ candidate đã xác minh khi revision/metadata/config còn hợp lệ. Crash sau rename thì đối chiếu receipt/state, vị trí và metadata trước khi encode lại; chưa đủ hồ sơ thì không tự công nhận thành công. Final đã commit hợp lệ và chỉ lỗi cleanup thì retry cleanup, không render lại.
### 14. `cleanup`
- depends_on: render_video đã verify và finalization thành công.
- input contract: finalization receipt, final hợp lệ, danh sách artifact do job sở hữu và cleanup/retention policy.
- output artifacts: cleanup_report.json, metadata/state cần giữ và final.mp4 được bảo toàn; temp lớn của job được xóa theo policy.
- cache key: Không dùng cache để bỏ qua kiểm tra filesystem cần cho việc dọn. Có thể hash dữ liệu nhỏ của finalization receipt + danh sách (artifact_id, revision) + cleanup policy để theo dõi attempt. Kiểm tra final qua manifest/size/mtime và chỉ xử lý danh sách đường dẫn job sở hữu; không đọc/hash nội dung media hoặc quét/hash toàn bộ thư mục chỉ để resume cleanup.
- failure/retry policy: Idempotent; file đã xóa được coi là đã dọn. Chỉ xóa tài nguyên tạm do job sở hữu; không xóa input local gốc, source media hoàn chỉnh tải từ URL hoặc final. Lỗi khóa file/quyền truy cập báo rõ và retry có giới hạn, không kéo theo encode lại. Đề xuất chỉ báo job SUCCESS sau cleanup thành công; nếu lỗi riêng cleanup thì giữ final hợp lệ, nút Thử lại tự chọn việc dọn còn thiếu, không yêu cầu người dùng chọn stage.
Cleanup sau FAILED hoặc CANCELLED không dùng dependency thành công ở trên: đó là đường xử lý trạng thái job/cache maintenance. Theo tài liệu hiện tại, failed cache giữ tối đa 24 giờ; cancel cleanup mặc định. Cả hai đường đều tuân thủ ownership, không xóa protected input và không xóa final hợp lệ đã công bố.

## Quyền sở hữu output và các lần sửa nội dung
Output			Nguồn dữ liệu được các bước sau sử dụng
transcript_raw.json	Kết quả nhận diện ban đầu, để dịch lần đầu và đối chiếu nguồn
translation_draft.json	Bản dịch lần đầu, chỉ là input của pre-TTS validation
segments_validated.json	Source/text đã được chấp nhận trước TTS; bao gồm source correction nếu có
dub_final.json	Text và audio cuối sau rewrite/re-TTS; là nguồn cho sync và subtitle
timing_final.json	Timing sau đồng bộ, dùng cho timeline và subtitle

Đặc biệt, rewrite sau TTS phải cập nhật đồng thời text cuối và audio reference. Nếu chỉ thay WAV nhưng subtitle vẫn dùng text cũ, pipeline chưa đúng contract.
Ví dụ phạm vi invalidation/khôi phục nội bộ; không phải các tùy chọn chọn stage hoặc sửa cấu hình trong GUI V1:
Thay đổi hoặc retry	Phần bị ảnh hưởng
Nhận diện tạo transcript mới	Nhánh dịch/validation/TTS/sync/subtitle/mix/render/cleanup; giữ kết quả separation còn hợp lệ
Background stem thay đổi	Mix, render, cleanup; giữ ASR/dịch/TTS/subtitle còn hợp lệ
Rewrite/re-TTS tạo dub revision mới	Sync, mix, subtitle, render, cleanup
Style subtitle khác trong một yêu cầu xử lý mới	Về dependency: subtitle, render, cleanup; GUI tạo job mới khi người dùng đổi cấu hình
Watermark khác trong một yêu cầu xử lý mới	Về dependency: render, cleanup; không chỉnh nguồn/cấu hình của job cũ

## Các quyết định sẽ chốt sau demo

Các nội dung sau được cố ý hoãn đến khi có bản demo end-to-end và dữ liệu benchmark thực tế:
- Các ngưỡng VAD/confidence/timing/stretch/overlap/loudness/verify.
- Vùng lấy frame OCR, số lần retry, số vòng rewrite/re-TTS và policy lỗi chất lượng.
- Thông số working audio theo từng adapter và phiên bản model/tool cụ thể.
- Ma trận hệ điều hành, CPU/GPU, RAM/VRAM, dung lượng, codec, quy trình cài đặt và phương án đóng gói.
- Rà soát license của code, model weights, FFmpeg build và các artifact được phân phối. Việc này phải hoàn tất trước public release; công nghệ không phù hợp sẽ được thay qua adapter tương ứng.
- Chuyển các NFR sơ bộ thành tiêu chí đo được và áp dụng đầy đủ vào code.

Main flow hiện đặc tả separation mặc định ON. Nếu sau demo bổ sung chế độ OFF, phải định nghĩa rõ cách tạo background và hành vi khi mất nền; không được âm thầm dùng audio nguồn còn lời Trung làm background.

