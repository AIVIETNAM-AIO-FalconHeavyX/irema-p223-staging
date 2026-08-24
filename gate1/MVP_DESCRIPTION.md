# MÔ TẢ CHI TIẾT MVP — VF-ONBOARDING COPILOT
## Tài liệu Nghiệp vụ & Kỹ thuật dành cho PM · Dev Lead · Tech Lead

| Trường | Nội dung |
| :--- | :--- |
| **Mã tài liệu** | MVP-DESC-VF-ONBOARDING-2026-V1 |
| **Phiên bản** | 1.0.0 |
| **Dự án** | VF-Onboarding Copilot — Team T223 |
| **Ngày soạn** | 09/08/2026 |
| **Tham chiếu** | MVP_SPEC_P1.md · PRD.md · SDD.md · brief.md |
| **Đối tượng đọc** | Project Manager · Tech Lead · Dev Lead · Product Owner |

> **Mục đích tài liệu:** Đây là tài liệu mô tả toàn diện hệ thống VF-Onboarding Copilot bằng ngôn ngữ văn xuôi — không chỉ là danh sách tính năng. Mỗi chức năng được diễn giải bối cảnh nghiệp vụ, lý do tồn tại, cách hoạt động chi tiết, và tiêu chí nghiệm thu. PM đọc để hiểu sản phẩm và quản lý tiến độ. Tech Lead đọc để nắm quyết định kiến trúc. Dev đọc để hiểu mục đích trước khi code.

---

## PHẦN I — TỔNG QUAN SẢN PHẨM

### 1. Bài toán gốc rễ và lý do tồn tại của sản phẩm

Hệ thống đại lý phân phối (ĐLPP) xe máy điện VinFast đang đối mặt với một vấn đề thực tế: kỹ thuật viên (KTV) mới không có chỗ tra cứu thông tin nhanh và đáng tin cậy. Mỗi khi gặp một mã lỗi trên xe, hoặc cần biết quy trình kiểm tra giao xe (PDI), KTV phải nhắn tin hoặc gọi điện cho quản lý xưởng — điều này không chỉ gián đoạn luồng sửa chữa mà còn tạo áp lực lên chuỗi hỗ trợ, kéo dài thời gian xử lý và tiềm ẩn rủi ro thao tác sai kỹ thuật. Đặc biệt nghiêm trọng trong bối cảnh xe máy điện vận hành với hệ thống pin cao áp, chỉ một lỗi thao tác có thể gây nguy hiểm trực tiếp cho người vận hành.

**VF-Onboarding Copilot** được sinh ra để giải quyết chính xác bài toán này: một trợ lý AI được nhúng vào xưởng dịch vụ, hoạt động 24/7, có khả năng trả lời câu hỏi kỹ thuật bằng tiếng Việt, trích dẫn nguồn tài liệu chính thức, và tự động cảnh báo an toàn khi cần. Quan trọng hơn, hệ thống biết *giới hạn của mình* — khi không đủ tự tin, nó không cố gắng đoán mò, mà chủ động chuyển hướng sang hỗ trợ người thật.

### 2. Đối tượng người dùng và phân quyền

Hệ thống Phase 1 phục vụ bốn nhóm người dùng nội bộ tại ĐLPP, mỗi nhóm có quyền truy cập thông tin khác nhau được kiểm soát chặt chẽ:

**Kỹ thuật viên (Technician)** là người dùng chính của hệ thống — họ làm việc trực tiếp tại xưởng, cần tra cứu nhanh quy trình bảo dưỡng, mã lỗi, và hướng dẫn PDI. Technician chỉ được xem tài liệu kỹ thuật cơ bản, không có quyền truy cập chính sách giá hay thông tin nội bộ quản lý.

**Tổ trưởng kỹ thuật (Lead Tech)** có quyền hạn mở rộng hơn — ngoài mọi tài liệu của KTV, họ được phép xem tài liệu sửa chữa chuyên sâu và quy trình phê duyệt bảo hành cấp 1. Lead Tech thường là người giải quyết các ca kỹ thuật phức tạp mà KTV leo thang lên.

**Quản lý xưởng (Service Manager)** có toàn quyền truy cập dữ liệu dịch vụ bao gồm chính sách bảo hành xưởng, quy định xuất vật tư và các tài liệu nghiệp vụ cấp quản lý. Đây là người giám sát toàn bộ hoạt động xưởng và cần thông tin đa chiều.

**Quản trị viên IT (IT Admin)** có quyền cao nhất — toàn quyền tra cứu cộng thêm vai trò tiếp nhận Support Ticket khi AI không tự xử lý được. IT Admin là lớp hỗ trợ cuối cùng trong hệ thống.

### 3. Tầm nhìn kiến trúc — tại sao lại chọn cách làm này?

Thay vì xây một chatbot đơn giản gửi câu hỏi thẳng vào LLM, đội ngũ kỹ thuật đã lựa chọn kiến trúc **Enterprise AI Production-Ready** với lý do rõ ràng: hệ thống phục vụ ngành kỹ thuật xe điện — nơi thông tin sai có thể gây tai nạn. Do đó, mọi quyết định thiết kế đều ưu tiên *độ chính xác*, *an toàn dữ liệu*, và *khả năng kiểm tra* lên trên tốc độ phát triển.

Kiến trúc này có ba đặc điểm nổi bật. Thứ nhất, luồng xử lý tài liệu (Ingestion) hoàn toàn tách biệt với luồng trả lời (Runtime) — admin có thể cập nhật tài liệu mà không cần restart hệ thống. Thứ hai, mọi request đi qua 10 lớp bảo vệ đầu vào và 7 lớp kiểm duyệt đầu ra trước khi đến tay người dùng. Thứ ba, hệ thống dùng Router thuật toán siêu nhẹ thay vì LLM để phân loại ý định câu hỏi, giúp giảm 60–70% chi phí token và giữ độ trễ tổng thể dưới 1.5 giây.

---

## PHẦN II — MÔ TẢ CHI TIẾT TỪNG TÍNH NĂNG (FEATURE)

---

### FEATURE 1: Hạ tầng & Môi trường Phát triển (MOD-01)

**Đây là nền móng của toàn bộ dự án.** Trước khi bất kỳ dòng code nào được viết, team cần thiết lập một môi trường làm việc thống nhất để tránh tình trạng "chạy được trên máy tôi nhưng không chạy được trên máy bạn" — một vấn đề kinh điển gây mất thời gian trong các dự án phần mềm.

Dev Lead (Hưng S) chịu trách nhiệm khởi tạo Git repository với chiến lược phân nhánh rõ ràng: nhánh `main` là code sản xuất, nhánh `develop` là nơi tích hợp tính năng, và mỗi developer làm việc trên feature branch riêng. Cấu trúc thư mục dự án cần được thỏa thuận giữa Tech Lead và Dev Lead ngay từ đầu — đây là quyết định ảnh hưởng đến toàn bộ vòng đời dự án. Biến môi trường `.env` phải có template mẫu nhưng tuyệt đối không được commit secret thật lên Git.

PM (Hưng) chịu trách nhiệm thiết lập Kanban board trên GitHub Projects với ba cột To Do / In Progress / Done, đảm bảo mọi tasks của 8 ngày đều có mặt và được phân ngày cụ thể để theo dõi tiến độ. Daily standup 15 phút mỗi sáng là nghi thức bắt buộc để team đồng bộ và phát hiện blockers sớm.

**Tiêu chí hoàn thành:** Toàn bộ thành viên clone repo và chạy được cả backend lẫn frontend trên máy local mà không cần hỏi ai.

---

### FEATURE 2: Xác thực vai trò và Phân quyền truy cập (MOD-02 — Authentication & RBAC)

**Đây là module bảo mật nền tảng, không thể thiếu.** Mục tiêu của RBAC (Role-Based Access Control) không chỉ là ngăn người không có quyền xem tài liệu nhạy cảm — quan trọng hơn, nó phải hoạt động đúng ngay cả khi có lỗi xảy ra. Nguyên tắc "fail-safe" nghĩa là: thà mặc định về quyền thấp nhất còn hơn để lọt dữ liệu.

Trong Phase 1, hệ thống nhận `user_role` trực tiếp từ request body (không cần JWT token phức tạp — đây là quyết định trade-off có chủ đích để MVP ra nhanh). Khi nhận được role, hệ thống tra cứu trong bảng phân cấp RBAC được định nghĩa cứng trong bộ nhớ để xác định người dùng được phép xem những loại tài liệu nào. Bảng phân cấp này là **business rule không được thay đổi** — mọi đề xuất sửa đổi phải qua PM phê duyệt.

Phân cấp cụ thể: IT Admin được xem tài liệu của tất cả các cấp. Service Manager được xem tài liệu của mình và tất cả cấp dưới. Lead Tech thấy được tài liệu của mình và KTV. Technician chỉ thấy tài liệu dành cho KTV và tài liệu công khai.

**Điều quan trọng cần lập trình viên nhớ:** Khi nhận role không hợp lệ (ví dụ ai đó gửi `user_role="hacker"`), hệ thống KHÔNG được trả lỗi — thay vào đó mặc định về `technician` (quyền thấp nhất) và ghi log WARNING. Đây là thiết kế cố ý: thà bị hạn chế quyền còn hơn để lỗ hổng bảo mật. Mọi exception trong RBAC đều phải được xử lý để không bao giờ "fail-open" (mở ra mặc định).

**Hiệu năng yêu cầu:** Toàn bộ logic xác thực phải hoàn thành dưới 1ms vì đây là tra cứu thuần túy trong bộ nhớ, không có bất kỳ I/O nào.

---

### FEATURE 3: Nạp tài liệu vào Knowledge Base (MOD-03 — Ingestion Pipeline)

**Đây là pipeline đưa "kiến thức" vào hệ thống.** Không có dữ liệu đúng thì AI không thể trả lời đúng — vì vậy Ingestion Pipeline là bước chuẩn bị có tính quyết định.

Luồng hoạt động bắt đầu từ PO (Chi) cung cấp tài liệu gốc dạng PDF, DOCX hoặc Excel — đây là tài liệu nội bộ của ĐLPP như hướng dẫn PDI, quy trình bảo dưỡng, bảng mã lỗi. PO không chỉ cung cấp file mà phải gán metadata cho mỗi tài liệu: tài liệu này dành cho role nào, thuộc chủ đề gì, áp dụng cho mẫu xe nào. Sau đó Tech Lead chạy pipeline xử lý offline (không cần internet, không gọi API ngoài) để cắt tài liệu thành các đoạn nhỏ (chunk) và lưu vào Knowledge Base.

Mỗi chunk không được vượt quá 500 tokens, với 50 tokens overlap giữa các chunk để đảm bảo không mất ngữ cảnh tại ranh giới. Hệ thống tự động phát hiện nội dung cảnh báo an toàn: bất kỳ chunk nào chứa các từ khóa như "CAUTION", "cảnh báo", "nguy hiểm", "pin cao áp", "high voltage" đều được gán thẻ `has_caution=true`. Thẻ này sau này sẽ kích hoạt banner cảnh báo màu đỏ trong giao diện.

Hệ thống tổ chức dữ liệu thành hai collections riêng biệt trong ChromaDB: `technician_docs` chứa tài liệu PDI và quy trình sửa chữa, `error_codes` chứa bảng mã lỗi DTC. Việc phân tách này giúp tối ưu tốc độ tìm kiếm.

**Thời hạn quan trọng:** PO phải hoàn tất chuẩn bị và gán metadata cho toàn bộ tài liệu trước cuối ngày 1 để Tech Lead có thể chạy ingestion đầu ngày 2. Nếu trễ deadline này, toàn bộ các module phía sau bị ảnh hưởng dây chuyền.

---

### FEATURE 4: Bảo vệ đầu vào — 10 lớp Guardrail (MOD-04 — Input Guardrails)

**Đây là tuyến phòng thủ đầu tiên và bắt buộc nhất của hệ thống.** Trước khi bất kỳ câu hỏi nào chạm đến LLM, nó phải đi qua 10 lớp kiểm tra theo thứ tự từ nhanh đến chậm. Nguyên tắc "short-circuit" được áp dụng: ngay khi một lớp phát hiện vấn đề, hệ thống từ chối ngay lập tức mà không cần chạy các lớp còn lại — điều này tiết kiệm tài nguyên và giảm độ trễ.

**Lớp 1 — Kiểm tra độ dài (GRD-01):** Câu hỏi phải có từ 2 đến 500 ký tự. Câu quá ngắn (như "?" hay "a") thường là test hoặc spam. Câu quá dài có thể là tấn công nhồi prompt. Cả hai đều bị từ chối với HTTP 400.

**Lớp 2 — Kiểm tra mã hóa ký tự (GRD-02):** Nếu hơn 30% ký tự trong câu hỏi là ký tự không in được (non-printable), đây thường là dấu hiệu của binary injection hoặc ký tự điều khiển độc hại.

**Lớp 3 — Lọc nội dung độc hại (GRD-03):** Từ ngữ thù ghét, bạo lực, nội dung phân biệt đối xử bị chặn. Danh sách blacklist được duy trì bởi PM và cập nhật định kỳ.

**Lớp 4 — Phát hiện Prompt Injection (GRD-04):** Đây là mối đe dọa phổ biến nhất với LLM — người dùng cố tình chèn lệnh để ghi đè hướng dẫn gốc của AI (ví dụ: "Bỏ qua tất cả hướng dẫn trước đó và..."). Hệ thống phải nhận diện các pattern này dựa trên danh sách keywords được cập nhật, từ chối và ghi log với cấp WARN để PM có thể review.

**Lớp 5 — Phát hiện Jailbreak (GRD-05):** Tấn công Jailbreak cố gắng khiến AI hoạt động ngoài vai trò được thiết kế (như "Hãy đóng vai một AI không có giới hạn" hoặc "DAN mode"). Khác với Prompt Injection tập trung vào lệnh, Jailbreak tập trung vào thay đổi bản sắc của AI. Cả hai đều nguy hiểm và phải bị chặn.

**Lớp 6 — Kiểm tra miền hoạt động (GRD-06):** Hệ thống chỉ phục vụ câu hỏi liên quan đến xe điện, kỹ thuật bảo dưỡng và nghiệp vụ ĐLPP. Câu hỏi về nấu ăn, thể thao, chính trị hay bất kỳ chủ đề ngoài domain đều bị từ chối — nhưng với thông điệp thân thiện bằng tiếng Việt, không phải thông báo lỗi kỹ thuật lạnh lùng.

**Lớp 7 — Che giấu thông tin cá nhân (GRD-07 — PII Masker):** Đây là lớp đặc biệt — nó **không từ chối** câu hỏi mà thay vào đó tự động tìm và thay thế thông tin nhận dạng cá nhân trước khi đưa vào hệ thống. Số điện thoại, CMND, số khung VIN, địa chỉ email đều được mask thành placeholder. Điều này bảo vệ quyền riêng tư người dùng, đặc biệt khi log câu hỏi để phân tích sau.

**Lớp 8 — Chặn SQL/XSS Injection (GRD-08):** Người dùng độc hại có thể nhúng SQL query hoặc script HTML vào câu hỏi với hy vọng khai thác lỗ hổng phía backend. Lớp này nhận diện các pattern nguy hiểm này và từ chối.

**Lớp 9 — Phát hiện Spam (GRD-09):** Giới hạn 20 request mỗi phút trên mỗi session, hoặc 3 câu hỏi giống hệt nhau trong lịch sử. Nếu vượt ngưỡng, trả HTTP 429 (Too Many Requests) thay vì 400 để phân biệt spam với lỗi nội dung.

**Lớp 10 — Tường lửa ngữ nghĩa (GRD-10 — Prompt Firewall):** Lớp cuối cùng và tốn kém nhất về tính toán — sử dụng embedding để so sánh ý nghĩa của câu hỏi với thư viện các intent nguy hiểm đã biết. Đây là lớp "net" để bắt các tấn công tinh vi mà các lớp keyword-based phía trên bỏ sót.

**Lưu ý hiệu năng:** Tổng thời gian xử lý 10 lớp phải dưới 80ms (GRD-01 đến GRD-09 dưới 30ms, riêng GRD-10 dưới 50ms). Đây là yêu cầu cứng vì guardrails không được làm tổng độ trễ E2E vượt 1.5 giây.

---

### FEATURE 5: Chuẩn hóa câu hỏi (MOD-05 — Query Normalizer)

**Kỹ thuật viên không viết câu hỏi như sách giáo khoa.** Họ viết tắt, dùng tiếng lóng kỹ thuật, và mix tiếng Anh vào tiếng Việt. Nếu không chuẩn hóa, hệ thống sẽ không tìm được thông tin dù tài liệu có đủ.

Query Normalizer thực hiện hai việc. Thứ nhất, mở rộng viết tắt chuyên ngành EV: "bms" thành "Battery Management System (BMS)", "pdi" thành "Pre-Delivery Inspection (PDI)", "ktv" thành "Kỹ thuật viên (KTV)", và nhiều từ viết tắt khác theo từ điển EV do PM (Hưng) duyệt. Thứ hai, thêm "role context hint" vào cuối câu hỏi để câu hỏi khi được tìm kiếm trong vector database có thêm ngữ cảnh — ví dụ KTV sẽ có thêm cụm "trong bối cảnh kỹ thuật viên sửa chữa tại xưởng dịch vụ" gắn vào, giúp kết quả retrieval phù hợp hơn với công việc thực tế của họ.

Module này không được dùng LLM, không có bất kỳ I/O nào — toàn bộ xử lý là pattern matching và string manipulation thuần túy, phải hoàn thành trong dưới 5ms. Điều quan trọng là module này không được thay đổi ý nghĩa của câu hỏi gốc — chỉ làm giàu thêm, không bóp méo.

---

### FEATURE 6: Bộ định tuyến Intent thông minh (MOD-06 — Lightweight Router)

**Đây là "não bộ" phân loại của hệ thống** — quyết định câu hỏi này cần xử lý theo hướng nào trong số 4 intent: hỏi về quy trình (WORKFLOW), hỏi về chính sách (RAG_POLICY), tra mã lỗi (ERROR_LOOKUP), hay cần tạo ticket hỗ trợ (STATIC_FORM).

Lý do phải có Router thay vì gửi thẳng vào RAG là tối ưu chi phí và tốc độ. Nếu câu hỏi là "quy trình PDI", không cần RAG phức tạp — chỉ cần lấy template tĩnh từ Workflow Skill. Nếu câu hỏi là "mã lỗi P0301", không cần RAG đầy đủ — chỉ cần tra bảng Error Lookup. Chỉ khi câu hỏi mơ hồ, liên quan đến chính sách hay quy định phức tạp thì mới cần RAG đầy đủ với LLM.

Router hoạt động theo 4 lớp ưu tiên. **Lớp 1 (Cache):** kiểm tra câu hỏi này đã được hỏi gần đây chưa, nếu có thì trả kết quả cache ngay (dưới 1ms). **Lớp 2 (Trie):** khớp keyword chính xác sử dụng cấu trúc dữ liệu Trie tối ưu — nếu tìm thấy với độ tự tin >= 90%, route ngay (dưới 10ms). Lớp này xử lý khoảng 75% traffic thực tế. **Lớp 3 (Embedding):** khi Trie không đủ tự tin, dùng vector embedding để so sánh ngữ nghĩa câu hỏi với các mẫu câu đặc trưng của từng intent (dưới 80ms). **Lớp 4 (LLM):** chỉ khi cả 3 lớp trên thất bại mới gọi LLM để phân loại — nhưng phải đảm bảo không quá 3% tổng traffic chạm đến lớp này. Nếu LLM timeout, mặc định về STATIC_FORM để người dùng tạo ticket thay vì nhận câu trả lời sai.

PM chịu trách nhiệm tổng hợp và xác nhận 30 câu hỏi kiểm tra (golden test set) — bao gồm cả câu rõ ràng, câu mơ hồ, và câu viết tắt tiếng Việt — để đo accuracy của Router. Accuracy phải đạt >= 90% mới được phép tích hợp vào pipeline chính.

---

### FEATURE 7: Bộ điều phối luồng xử lý (MOD-07 — Orchestration Engine)

**Orchestration Engine là "nhạc trưởng" của toàn bộ hệ thống.** Nó không xử lý logic nghiệp vụ — nó chỉ điều phối dữ liệu qua đúng thứ tự các bước xử lý theo cấu trúc StateGraph.

Mọi thông tin cần thiết để xử lý một request được gói trong một đối tượng `AgentState` — đây là "hồ sơ sống" của request, được truyền từ node này sang node khác và bổ sung thêm thông tin ở mỗi bước. AgentState bao gồm: câu hỏi gốc, role người dùng, kết quả phân loại từ Router, các chunks tài liệu được retrieve, câu trả lời từ Skill, và cờ điều khiển (có cần CAUTION không, có cần escalate không).

Luồng cố định: mọi request đều đi qua Input Guardrails → Normalizer → Router. Sau đó Router tách ra: WORKFLOW đến Workflow Skill, RAG_POLICY đến Policy Copilot Skill, ERROR_LOOKUP đến Error Lookup Skill, STATIC_FORM đến Ticket Skill. Sau khi Skill trả kết quả, luồng hội tụ lại tại Output Guardrails. Nếu Output Guardrails phát hiện cần escalation, tự động chuyển sang Ticket Skill. Cuối cùng, Response Formatter định dạng kết quả và trả về người dùng.

**Nguyên tắc thiết kế bắt buộc:** Không được đặt bất kỳ business logic nào trong file điều phối lõi. Orchestration Engine chỉ định tuyến — mọi quyết định nghiệp vụ phải nằm trong các module chuyên biệt. Điều này đảm bảo hệ thống dễ test và dễ thay thế từng module.

---

### FEATURE 8: Hướng dẫn quy trình từng bước (MOD-08 — Workflow Skill)

**Workflow Skill giải quyết nhóm câu hỏi "Tôi cần làm gì và làm thế nào?"** — loại câu hỏi phổ biến nhất từ KTV mới. Ví dụ: "Quy trình PDI xe Klara S gồm những bước nào?" hay "Quy trình bảo dưỡng pin LFP định kỳ là gì?"

Điểm đặc biệt của module này là nó **không dùng LLM** — câu trả lời được lấy trực tiếp từ các template YAML được soạn sẵn và đã được phê duyệt nội dung. Điều này đảm bảo 100% độ chính xác (không có hallucination) và tốc độ cực nhanh (dưới 50ms). Trade-off là nội dung không linh hoạt — nhưng trong bối cảnh quy trình kỹ thuật chuẩn, đây lại là ưu điểm vì không ai muốn AI "sáng tạo" ra các bước quy trình.

PO (Chi) chịu trách nhiệm soạn ít nhất 3 template workflows trước ngày 3: quy trình PDI xe Klara S (khoảng 10 bước), quy trình bảo dưỡng pin LFP định kỳ (khoảng 7 bước), và quy trình tiếp nhận xe hỏng (khoảng 5 bước). Mỗi bước phải có tiêu đề, mô tả chi tiết, và thời gian ước tính. Nếu workflow liên quan đến điện cao áp, phải có `has_caution=true` và `caution_message` rõ ràng.

RBAC được áp dụng tại đây: Technician không thể xem workflow dành cho Service Manager. Khi một workflow không tồn tại, thay vì báo lỗi, hệ thống liệt kê danh sách các workflow có sẵn để người dùng chọn — trải nghiệm này thân thiện hơn nhiều.

---

### FEATURE 9: Trợ lý tra cứu chính sách bằng AI (MOD-09 — Policy Copilot Skill / RAG)

**Đây là tính năng phức tạp và có giá trị nhất của hệ thống.** Policy Copilot cho phép người dùng đặt câu hỏi tự nhiên về chính sách, quy định, hướng dẫn kỹ thuật — và nhận câu trả lời được tổng hợp từ đúng tài liệu, kèm trích dẫn nguồn cụ thể.

Luồng xử lý RAG gồm nhiều bước tinh tế. Bước đầu, hệ thống lấy câu hỏi đã chuẩn hóa và role của người dùng từ AgentState. Bước tiếp theo là Hybrid Search — đồng thời tìm kiếm bằng từ khóa (để bắt chính xác thuật ngữ kỹ thuật) và tìm kiếm ngữ nghĩa (để hiểu câu hỏi viết không đúng kỹ thuật). Quan trọng: bộ lọc RBAC được áp dụng ngay tại bước tìm kiếm — ChromaDB chỉ trả về chunks mà role của người dùng có quyền xem. Không có bước "lọc sau" nào — dữ liệu nhạy cảm không bao giờ được tải lên để rồi bị lọc đi.

Sau khi có kết quả từ hai phương pháp tìm kiếm, chúng được kết hợp bằng thuật toán RRF (Reciprocal Rank Fusion) và được Cross-Encoder Reranker chấm điểm lại để chọn ra 3 chunks liên quan nhất. Hệ thống tính `retrieval_confidence` dựa trên điểm cosine similarity trung bình.

Đây là điểm quyết định: nếu confidence < 0.70, hệ thống đặt cờ `need_escalation=True` và **không cố gắng trả lời**. Đây là thiết kế có chủ đích — thà thừa nhận không biết còn hơn bịa ra thông tin sai. Khi confidence >= 0.70, các chunks được đưa vào prompt của LLM để tổng hợp câu trả lời cuối cùng bằng tiếng Việt, kèm trích dẫn định dạng `[STT] TênFile — Trang/Sheet X`.

**PM (Hưng) chịu trách nhiệm soạn và duyệt system prompt** cho LLM vào ngày 4 — đây là văn bản hướng dẫn hành vi của AI, không được để Tech Lead tự quyết định mà không có sự đồng thuận của PM.

---

### FEATURE 10: Tra cứu mã lỗi kỹ thuật (MOD-10 — Error Lookup Skill)

**Khi một xe báo lỗi tại xưởng, mỗi phút đều có giá trị.** Error Lookup Skill được thiết kế để trả kết quả trong vòng 200ms cho mọi mã lỗi có trong hệ thống — nhanh hơn bất kỳ hướng dẫn thủ công nào.

Module này có hai luồng xử lý. Luồng chính là **Exact Match**: hệ thống dùng regular expression để nhận diện mã lỗi DTC trong câu hỏi (các pattern như P0xxx, E0xxx, BMS_XXXX, Uxxxx, Bxxxx). Khi tìm thấy mã, hệ thống tra thẳng vào Knowledge Base theo ID và trả kết quả ngay — không qua LLM, không cần inference, chỉ là database lookup. Nếu không có mã lỗi rõ ràng, luồng dự phòng là **Semantic Search**: người dùng mô tả triệu chứng ("xe không khởi động được", "màn hình báo nhấp nháy") và hệ thống gợi ý 3-5 mã lỗi có thể liên quan.

Mọi mã lỗi liên quan đến điện cao áp hoặc BMS pin bắt buộc phải kèm **CAUTION banner** ở đầu câu trả lời — trước mọi thông tin khác. Banner này màu đỏ, font đậm, nội dung cảnh báo an toàn rõ ràng. Đây không phải tùy chọn mà là yêu cầu an toàn bắt buộc.

Câu trả lời cho mỗi mã lỗi phải đầy đủ 6 trường: Mô tả lỗi, Nguyên nhân thường gặp, Các bước xử lý (checklist), Thời gian ước tính xử lý, Linh kiện có thể cần thay, và Nguồn tài liệu tham chiếu. Nếu mã không tồn tại trong hệ thống, trả thông báo rõ ràng và đề xuất tạo ticket để IT Admin hỗ trợ.

**PO (Chi) phải chuẩn bị ít nhất 50 mã lỗi** (30 P-code, 10 BMS-code, 10 E-code) trước ngày 1 với đầy đủ thông tin cho từng mã. Đây là dữ liệu quan trọng nhất của toàn hệ thống về mặt an toàn kỹ thuật.

---

### FEATURE 11: Biểu mẫu Hỗ trợ và Tạo Ticket (MOD-11 — Static Form / Ticket Skill)

**Đây là "lưới an toàn" của toàn hệ thống — fail-safe mechanism được thiết kế cẩn thận.** Khi AI không đủ tự tin, thay vì im lặng hoặc trả lời sai, hệ thống chuyển người dùng sang kênh hỗ trợ người thật với đầy đủ ngữ cảnh đã được điền sẵn.

Có bốn tình huống kích hoạt Static Form. Đầu tiên là khi RAG confidence dưới 0.70 — hệ thống tự động phát hiện mình không đủ tự tin và chuyển hướng. Thứ hai là khi Error Lookup không tìm thấy mã lỗi. Thứ ba là khi Output Guardrail phát hiện hallucination trong câu trả lời. Thứ tư là khi người dùng chủ động yêu cầu hỗ trợ thêm — điều này quan trọng vì người dùng luôn có quyền quyết định cần con người hỗ trợ.

Form được thiết kế thông minh để giảm ma sát cho người dùng: nhiều trường được điền tự động từ context của cuộc hội thoại. Câu hỏi gốc, mã lỗi đã phát hiện, và mô tả triệu chứng được lấy từ AgentState và điền vào form. Người dùng chỉ cần bổ sung tên, mẫu xe, và số liên hệ.

Sau khi submit, hệ thống tạo ticket với mã định danh duy nhất (format TCK-YYYYMMDD-XXXXXX), tự động phân loại độ ưu tiên (urgent/high/normal) dựa trên nội dung, và push ngay lên màn hình quản trị của IT Admin. Ticket liên quan đến điện cao áp tự động được đánh ưu tiên "urgent" với SLA phản hồi 1 giờ — vì đây là vấn đề an toàn.

---

### FEATURE 12: Tìm kiếm Hybrid trong Knowledge Base (MOD-12 — Retrieval Pipeline)

**Tại sao lại cần cả hai loại tìm kiếm?** Đây là câu hỏi quan trọng về mặt kỹ thuật mà PM và Dev cần hiểu.

Tìm kiếm từ khóa (Keyword/Lexical Search bằng BM25) xuất sắc khi người dùng dùng thuật ngữ chính xác như "P0301" hay "BMS_OVERHEAT" — nó tìm được chunk chứa đúng chuỗi ký tự đó. Nhưng nó thất bại khi người dùng diễn đạt khác đi: "xe không khởi động được sáng nay" không có từ khóa kỹ thuật nào để match.

Tìm kiếm ngữ nghĩa (Semantic/Vector Search) xuất sắc ở chiều ngược lại — nó hiểu "xe không khởi động được" và "engine failure to start" có cùng ý nghĩa, kể cả khi từ ngữ hoàn toàn khác nhau. Nhưng nó thất bại với mã lỗi chính xác vì các con số và ký tự đặc biệt không mang nhiều ý nghĩa ngữ nghĩa.

Hybrid Search kết hợp cả hai và dùng Cross-Encoder Reranker để đánh giá lại kết quả tổng hợp — cho phép hệ thống xử lý tốt cả câu hỏi kỹ thuật chính xác lẫn câu hỏi mô tả triệu chứng tự nhiên. Đây là lý do tại sao retrieval cần là Hybrid, không phải chỉ một phương pháp.

Pipeline đảm bảo RBAC được áp dụng trước tiên — chỉ tìm kiếm trong tập chunks mà role của người dùng có quyền truy cập. Đây là kiểm soát ở tầng data, không phải tầng application — cho phép bảo mật ngay cả khi có lỗi ở tầng trên.

---

### FEATURE 13: Tích hợp LLM và Kiểm duyệt đầu ra (MOD-13 — LLM Integration & Output Guardrails)

**Gọi LLM là bước đắt nhất và rủi ro nhất trong pipeline.** Module này quản lý cả việc gọi LLM lẫn việc kiểm tra kết quả trước khi trả về người dùng.

Về chiến lược LLM: hệ thống dùng hai service với cơ chế tự động fallback. Khi service chính gặp sự cố (timeout, rate limit, lỗi API), hệ thống tự chuyển sang service dự phòng mà không cần can thiệp thủ công. Context được giới hạn 2000 tokens để kiểm soát chi phí và giúp LLM tập trung.

Sau khi LLM tạo ra câu trả lời, 7 lớp Output Guardrails kiểm tra trước khi trả về người dùng:

**OUT-01 (Citation Requirement):** Câu trả lời kỹ thuật phải có ít nhất một trích dẫn nguồn. Nếu LLM trả về câu trả lời không có citation, coi đó là hallucination tiềm năng, hủy và escalate.

**OUT-02 (Hallucination Detector):** So sánh nội dung câu trả lời với các chunks tài liệu gốc bằng vector similarity. Nếu câu trả lời chứa thông tin không xuất hiện trong nguồn tài liệu, phát hiện là hallucination và escalate sang Static Form.

**OUT-03 (RBAC Leak Checker):** Kiểm tra câu trả lời không vô tình chứa thông tin từ tài liệu ngoài quyền của người dùng. Đây là lớp double-check sau khi RBAC đã được áp dụng ở tầng retrieval.

**OUT-04 (Safety Validator):** Phát hiện câu trả lời chứa hướng dẫn nguy hiểm (ví dụ: hướng dẫn tiếp xúc trực tiếp với pin cao áp mà không có thiết bị bảo hộ). Nếu phát hiện, hoặc thêm CAUTION banner, hoặc hủy câu trả lời tùy mức độ nguy hiểm.

**OUT-05 (Language Checker):** Hệ thống chỉ phục vụ bằng tiếng Việt. Nếu LLM trả lời bằng ngôn ngữ khác, yêu cầu regenerate.

**OUT-06 (Length Checker):** Câu trả lời quá dài (hơn 1500 từ) thường là dấu hiệu LLM "nói nhiều" hoặc lặp lại. Hệ thống truncate và yêu cầu tóm tắt.

**OUT-07 (PII Output Checker):** Tương tự Input Guardrail GRD-07 nhưng áp dụng cho output — đảm bảo LLM không vô tình trích xuất và hiển thị thông tin cá nhân từ tài liệu.

---

### FEATURE 14: Định dạng và trình bày kết quả (MOD-14 — Response Formatter)

**Cùng một thông tin nhưng trình bày khác nhau tạo ra trải nghiệm người dùng hoàn toàn khác nhau.** Response Formatter chuyển đổi dữ liệu thô từ Skills thành nội dung hiển thị phù hợp với từng loại intent.

Câu trả lời về quy trình (WORKFLOW) được trình bày dạng Markdown checklist có thể check-off từng bước. Câu trả lời chính sách (RAG_POLICY) là đoạn văn mạch lạc kèm accordion citations có thể click mở ra xem nguồn gốc. Kết quả tra mã lỗi (ERROR_LOOKUP) là bảng có cấu trúc rõ ràng với 6 trường thông tin. Static Form được trình bày dạng modal popup với các trường đã điền sẵn.

CAUTION banner là thành phần UI có spec rõ ràng nhất: màu nền đỏ nhạt, chữ đậm màu đỏ đậm, icon cảnh báo, và phải hiển thị ở **đầu tiên** trước mọi nội dung khác khi `has_caution=true`. Không có ngoại lệ.

---

### FEATURE 15: Giao diện Chat người dùng (MOD-15 — Frontend Chat UI)

**Giao diện là điểm tiếp xúc duy nhất giữa người dùng và hệ thống.** Dù backend mạnh mẽ đến đâu, nếu UI không thân thiện, người dùng sẽ không sử dụng.

**Role Selector (P0 — phải có):** Dropdown chọn vai trò khi vào hệ thống — đây là bước đầu tiên bắt buộc vì role quyết định mọi thứ trong pipeline. Role được gán vào tất cả API request sau đó.

**Chat Window (P0):** Khung hội thoại với bubble messages, phân biệt message của người dùng và AI. Hỗ trợ render Markdown vì câu trả lời từ AI sẽ có định dạng phức tạp.

**CAUTION Banner (P0):** Banner đỏ nổi bật với icon cảnh báo — đây là yêu cầu an toàn, không phải trang trí. Phải đủ nổi bật để không thể bỏ qua.

**Citation Accordion (P0):** Phần trích dẫn nguồn có thể click để mở/đóng. Mặc định đóng để không làm rối giao diện, nhưng người dùng luôn có thể xem nguồn gốc thông tin.

**Static Form Modal (P0):** Popup form xuất hiện khi cần escalation, với các trường đã điền sẵn từ context chat. Người dùng chỉ cần bổ sung thông tin còn thiếu.

**Ticket Confirmation (P0):** Màn hình xác nhận sau khi submit ticket, hiển thị mã ticket để người dùng theo dõi.

**Loading Skeleton (P1):** Animation khi AI đang xử lý — quan trọng vì tổng latency có thể lên đến 1.5 giây, người dùng cần biết hệ thống đang hoạt động.

Yêu cầu responsive: giao diện phải hoạt động tốt trên màn hình từ 375px (iPhone SE) trở lên — KTV thường dùng điện thoại trong xưởng, không phải desktop.

---

### FEATURE 16: API Gateway (MOD-16 — Backend REST API)

**API Layer là cầu nối giữa Frontend và toàn bộ pipeline AI.** Mọi request từ browser đi qua API này trước khi vào hệ thống.

Endpoint chính là `POST /api/v1/chat` — nhận câu hỏi, role người dùng, và session_id; trả về câu trả lời, danh sách citations, confidence score, ticket_id (nếu được tạo), cờ caution, và thời gian xử lý. Hệ thống ticket có ba endpoints: POST để tạo ticket mới, GET để IT Admin xem danh sách tickets, PATCH để cập nhật trạng thái ticket.

CORS phải được cấu hình đúng để chỉ cho phép domain Frontend giao tiếp. Rate limiting 20 request mỗi phút mỗi session được implement ở tầng API. Health check endpoint `/api/v1/health` trả 200 OK để monitoring service có thể kiểm tra hệ thống còn sống.

---

### FEATURE 17: Kiểm thử và Đảm bảo chất lượng (MOD-17 — Testing & QA)

**QA không phải bước cuối — nó là quá trình liên tục trong suốt 8 ngày.** Tuy nhiên ngày 7 là ngày "Full QA Gate" — toàn bộ team tập trung kiểm tra tất cả tiêu chí nghiệm thu.

Kiểm thử được phân công rõ ràng theo ngày: Ngày 3 PM đo accuracy Router; Ngày 4 PO kiểm tra RAG citations và RBAC; Ngày 5 PM đo Error Lookup latency và PO test Static Form; Ngày 6 PO chạy E2E test 4 luồng; Ngày 7 PM + PO chạy Full QA Gate checklist.

**Checklist QA Gate ngày 7 bao gồm 9 tiêu chí cứng:** Router accuracy >= 90%, RAG luôn có citations, RBAC không leak, Error Lookup < 200ms, 10/10 attack vectors bị chặn, Static Form submit thành công, Latency E2E < 1.5s, Mobile responsive >= 375px, và Hallucination rate <= 1%.

**Điều kiện then chốt:** Nếu BẤT KỲ tiêu chí nào thất bại, KHÔNG được phép deploy ngày 8. PM phải sắp xếp ngay hotfix và đánh giá lại timeline.

---

### FEATURE 18: Triển khai và Go-live (MOD-18 — Deployment & Go-live)

**Ngày 8 là Demo Day — hệ thống phải live và ổn định.** Backend deploy lên Render.com, Frontend deploy lên Vercel. Biến môi trường phải được cấu hình qua environment variables của platform — tuyệt đối không hardcode trong source code.

PO chịu trách nhiệm smoke test trên Live URL — chạy 4 luồng demo chính. **Demo script 5 phút** được thiết kế để thể hiện đầy đủ giá trị của hệ thống: bắt đầu với onboarding KTV mới → tra mã lỗi BMS_OVERHEAT với CAUTION banner đỏ → hỏi quy trình PDI Klara S với citations → gặp câu hỏi mơ hồ dẫn đến Static Form popup auto-fill → điền và submit ticket. Đây là hành trình người dùng thực tế, không phải demo kỹ thuật.

---

## PHẦN III — KPI VÀ TIÊU CHÍ NGHIỆM THU TỔNG HỢP

### KPIs sản phẩm (đo sau Go-live 30 ngày)

| Chỉ số | Mục tiêu | Cách đo |
| :--- | :--- | :--- |
| **AI Deflection Rate** | >= 60% | % câu hỏi AI tự giải quyết / tổng câu hỏi |
| **Time-to-Onboard KTV mới** | < 2 ngày (giảm từ 5 ngày) | Survey với KTV mới |
| **Hallucination Rate** | <= 1% | Human review ngẫu nhiên 100 responses |
| **Latency E2E (P95)** | < 1.5 giây | Đo từ log latency_ms |
| **Router Latency** | < 100ms | Đo riêng router_latency trong log |
| **Token Cost Reduction** | 60-70% | So sánh chi phí với baseline LLM-Router |

### Acceptance Criteria bắt buộc trước Release

Hệ thống chỉ được phép Go-live khi tất cả 6 tiêu chí sau đều đạt:

1. Smart Router đạt độ chính xác phân loại >= 90% trong < 100ms trên bộ 30 golden queries.
2. Hệ thống vượt qua toàn bộ 10/10 kịch bản tấn công Prompt Injection và Jailbreak.
3. 100% câu trả lời nghiệp vụ từ Policy Copilot có ít nhất một trích dẫn nguồn.
4. Tài khoản Technician tuyệt đối không truy xuất được tài liệu của Service Manager.
5. Khi RAG Confidence < 0.70, Static Form Ticket tự động hiển thị trong vòng 2 giây.
6. Latency End-to-End P95 < 1.5 giây.

---

## PHẦN IV — PHÂN TÍCH RỦI RO VÀ BIỆN PHÁP GIẢM THIỂU

| Rủi ro | Mức độ | Biện pháp |
| :--- | :--- | :--- |
| **LLM Hallucination** — AI bịa thông tin kỹ thuật sai, nguy hiểm trong bối cảnh xe điện | CAO | Output Guardrail OUT-02 bắt buộc đối chiếu citation; threshold 0.70 khắt khe; escalate thay vì đoán |
| **Rò rỉ dữ liệu phân quyền** — Technician thấy thông tin Manager | CAO | RBAC enforce ở tầng ChromaDB; double-check bởi OUT-03 output guardrail |
| **LLM Provider Downtime** — Gemini/Claude bị sự cố | TRUNG BÌNH | Chain Fallback tự động; Workflow và Error Lookup không phụ thuộc LLM vẫn hoạt động |
| **Độ trễ tăng do Guardrails** — 17 lớp kiểm tra cộng thêm ms | TRUNG BÌNH | Input Guardrails < 80ms; bù đắp bằng Router Trie (< 10ms) thay vì LLM Router (> 1s) |
| **Chất lượng tài liệu đầu vào kém** — PDF scan mờ, metadata thiếu | TRUNG BÌNH | PO xong ngày 1; Tech Lead review chất lượng trước khi ingestion |

---

## PHẦN V — TIMELINE 8 NGÀY VÀ DEPENDENCY MAP

```
Ngày 1: [MOD-01 Hạ tầng] [MOD-02 RBAC bắt đầu] [PO: Chuẩn bị tài liệu + mã lỗi]
Ngày 2: [MOD-02 RBAC xong] [MOD-03 Ingestion] [MOD-05 Normalizer] [MOD-16 API skeleton]
Ngày 3: [MOD-06 Router 4-layer] [MOD-04 Guardrails bắt đầu] [PM: Router accuracy test]
Ngày 4: [MOD-04 Guardrails xong] [MOD-09 RAG] [MOD-12 Hybrid Search] [MOD-08 Workflow]
Ngày 5: [MOD-10 Error Lookup] [MOD-11 Static Form] [MOD-13 LLM+OutputGuard bắt đầu]
Ngày 6: [MOD-07 Orchestration E2E] [MOD-13 xong] [MOD-14 Formatter] [MOD-15 UI polish]
Ngày 7: [MOD-17 Full QA Gate] [Bug fix sprint]
Ngày 8: [MOD-18 Deploy lên production] [Demo Day]
```

**Dependency cứng PM phải theo dõi hàng ngày:**

1. **PO xong tài liệu cuối ngày 1** → MOD-03 có thể chạy đầu ngày 2.
2. **MOD-03 Ingestion xong** → MOD-09 RAG và MOD-10 Error Lookup mới có data để test.
3. **PM xong golden test set cuối ngày 2** → MOD-06 Router có thể đo accuracy ngày 3.
4. **MOD-06 Router xong ngày 3** → MOD-07 Orchestration tích hợp đầy đủ ngày 5-6.
5. **Full QA Gate ngày 7 PASS** → Deploy ngày 8 được phép. Nếu FAIL → không deploy, hotfix.

---

## PHẦN VI — MA TRẬN RACI

| Module | PM (Hưng) | PO (Chi) | Tech Lead (Thái) | Dev Lead (Hưng S) |
| :--- | :---: | :---: | :---: | :---: |
| MOD-01 Hạ tầng | A | - | C | **R** |
| MOD-02 RBAC | A | - | **R** | C |
| MOD-03 Ingestion | I | **R** (nội dung) | **R** (code) | C |
| MOD-04 Guardrails | A | I | **R** | C |
| MOD-05 Normalizer | **R** (từ điển EV) | C | **R** (code) | I |
| MOD-06 Router | A (validate accuracy) | **R** (test data) | **R** | I |
| MOD-07 Orchestration | I | I | **R** | C |
| MOD-08 Workflow | I | **R** (nội dung template) | C | **R** (code) |
| MOD-09 Policy RAG | **R** (soạn prompt) | I | **R** | C |
| MOD-10 Error Lookup | I | **R** (data mã lỗi) | **R** (code) | C |
| MOD-11 Static Form | I | I | C | **R** |
| MOD-12 Retrieval | I | I | **R** | C |
| MOD-13 LLM + Output | I | I | **R** | C |
| MOD-14 Formatter | I | I | C | **R** |
| MOD-15 Frontend UI | I | **R** (UAT) | C | **R** |
| MOD-16 API Layer | I | I | C | **R** |
| MOD-17 Testing & QA | A | **R** | **R** | **R** |
| MOD-18 Deployment | A | R (smoke test) | C | **R** |

> **R** = Responsible (người thực hiện) · **A** = Accountable (người chịu trách nhiệm) · **C** = Consulted · **I** = Informed

---

## PHẦN VII — GLOSSARY (Từ điển thuật ngữ)

Phần này dành cho PM và PO không có background kỹ thuật sâu.

| Thuật ngữ | Giải thích đơn giản |
| :--- | :--- |
| **RAG (Retrieval-Augmented Generation)** | Phương pháp cho AI trả lời dựa trên tài liệu được cung cấp, không tự "bịa ra" kiến thức. Giống như cho AI xem sách trước khi trả lời. |
| **LLM (Large Language Model)** | Mô hình AI ngôn ngữ lớn — ví dụ Gemini hay Claude — có khả năng hiểu và tạo ra văn bản tự nhiên. |
| **Vector Embedding** | Cách biểu diễn ý nghĩa của văn bản bằng con số, để hai câu có cùng ý nghĩa sẽ "gần nhau" trong không gian số học. |
| **Hybrid Search** | Kết hợp tìm kiếm từ khóa chính xác (BM25) và tìm kiếm ngữ nghĩa (Vector) để đạt kết quả tốt nhất. |
| **RBAC** | Phân quyền theo vai trò — ai có role gì thì chỉ xem được tài liệu dành cho role đó. |
| **Hallucination** | Khi AI tạo ra thông tin nghe có vẻ đúng nhưng thực ra không có trong nguồn tài liệu. Đây là rủi ro chính của LLM. |
| **Guardrails** | Các lớp kiểm tra bảo vệ hệ thống — input guardrails kiểm tra câu hỏi đầu vào, output guardrails kiểm tra câu trả lời. |
| **DTC Code** | Diagnostic Trouble Code — mã lỗi tiêu chuẩn của xe, ví dụ P0301 hay BMS_OVERHEAT. |
| **PDI** | Pre-Delivery Inspection — quy trình kiểm tra xe trước khi giao cho khách hàng. |
| **Confidence Score** | Điểm tự tin của hệ thống (0 đến 1). Dưới 0.70 là không đủ tự tin, hệ thống sẽ escalate. |
| **Latency / P95** | Độ trễ — thời gian từ khi gửi câu hỏi đến khi nhận câu trả lời. P95 = 95% requests dưới ngưỡng này. |
| **Prompt Injection** | Tấn công cố tình thêm lệnh ẩn vào câu hỏi để thao túng hành vi của AI. |
| **Jailbreak** | Tấn công cố thay đổi "nhân cách" của AI để nó bỏ qua các giới hạn an toàn. |
| **PII** | Personally Identifiable Information — thông tin nhận dạng cá nhân như CMND, SĐT, VIN, email. |
| **BMS** | Battery Management System — hệ thống quản lý pin của xe điện. |
| **KTV / DLPP** | Kỹ thuật viên / Đại lý Phân phối — thuật ngữ nội bộ VinFast. |
| **Escalation** | Chuyển vấn đề lên cấp cao hơn (từ AI sang người thật) khi AI không xử lý được. |
| **Trie** | Cấu trúc dữ liệu cây tối ưu cho tìm kiếm từ khóa nhanh — dùng trong Router Lớp 2. |
| **RRF (Reciprocal Rank Fusion)** | Thuật toán kết hợp kết quả tìm kiếm từ nhiều phương pháp thành một danh sách xếp hạng chung. |
| **Cross-Encoder Reranker** | Mô hình AI nhỏ dùng để đánh giá lại và sắp xếp thứ tự các kết quả tìm kiếm theo độ liên quan. |
| **AgentState** | "Hồ sơ sống" của một request — đối tượng chứa toàn bộ thông tin được truyền qua các bước xử lý. |
| **Fail-safe** | Nguyên tắc thiết kế: khi có lỗi, mặc định về trạng thái an toàn nhất thay vì mở rộng quyền truy cập. |
| **StateGraph** | Cấu trúc đồ thị trạng thái dùng để định nghĩa luồng xử lý trong Orchestration Engine. |

---

*Tài liệu: MVP-DESC-VF-ONBOARDING-2026-V1*
*Soạn ngày: 09/08/2026 — Dự án: VF-Onboarding Copilot — Team T223*
*Đối tượng: Project Manager · Tech Lead · Dev Lead · Product Owner*
