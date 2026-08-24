# MVP SPECIFICATION — PHASE 2 EXTENSION CONTRACTS
## VF-Onboarding Copilot — Future Roadmap Specification

| Truong | Noi dung |
| :--- | :--- |
| **Ma tai lieu** | MVP-SPEC-P2-VF-ONBOARDING-2026-V1 |
| **Phien ban** | 1.0.0 |
| **Pham vi** | Phase 2 Extensions — Post-MVP Roadmap |
| **Ngay phat hanh** | 09/08/2026 |
| **Trang thai** | Extension Contract Only — Do NOT implement in Phase 1 |
| **Tham chieu** | MVP_SPEC.md (Tong quan) · MVP_SPEC_P1.md (Phase 1 Chi tiet) · SDD.md (Technical) |

> **Muc dich tai lieu nay:**
> Mo ta cac tinh nang Phase 2 o muc do "Extension Contract" — du ro rang ve WHAT va WHY de planning,
> nhung chua di vao implementation detail. Kien truc Phase 1 duoc thiet ke de cac module nay
> co the plug-in ma khong can refactor core.

> **Luu y quan trong cho PM:**
> Phase 2 chi bat dau sau khi Phase 1 da on dinh >= 30 ngay van hanh thuc te tai DLPP.
> Khong duoc voi vang implement truoc khi co du lieu van hanh de ra quyet dinh dung.

---

## Dieu kien bat dau Phase 2 (Go/No-Go Criteria)

Truoc khi bat dau bat ky module Phase 2 nao, phai dat du cac chi so sau day:

| Chi so | Nguong bat dau Phase 2 |
| :--- | :--- |
| Phase 1 van hanh on dinh | >= 30 ngay khong co critical bug |
| AI Deflection Rate | >= 60% (AI tu xu ly khong can tao Ticket) |
| Hallucination Rate | <= 1% |
| User Satisfaction (DLPP pilot) | >= 4.0/5.0 tu khao sat |
| Latency P95 | < 1.5s lien tuc |

---

## Muc luc Phase 2 Extensions

| ID | Ten Module | Do uu tien | Dieu kien bat dau |
| :--- | :--- | :--- | :--- |
| P2-01 | Voice AI (STT/TTS) | Cao | Phase 1 on dinh, DLPP co nhu cau voice |
| P2-02 | OCR Error Extractor | Cao | Pilot DLPP co camera, co data anh man hinh |
| P2-03 | QR Code Vehicle Resolver | Trung binh | Hardware QR scanner tai DLPP |
| P2-04 | Image Understanding | Thap | Can model multimodal tot tieng Viet |
| P2-05 | Advanced Memory | Trung binh | Du du lieu conversation de train |
| P2-06 | Multi-Agent Orchestration | Thap | Khi so luong Skills > 8 |
| P2-07 | History-Augmented RAG | Trung binh | Sau khi do duoc conversation quality |
| P2-08 | Dashboard & Analytics | Cao | >= 30 ngay du lieu van hanh |
| P2-09 | Sales/Pricing Module | Trung binh | Bo phan Sales yeu cau |
| P2-10 | Manager Dashboard | Trung binh | Service Manager yeu cau |
| P2-11 | Offline Mode (Web App nội bộ + AI cục bộ) | Thap | DLPP o vung internet kem |
| P2-12 | Voice Cloning | Thap | Yeu cau cu the tu DLPP |

---

## P2-01: Voice AI (STT/TTS)

### Tong quan

**Van de giai quyet:**
KTV dang lam viec tay ban, khong the go ban phim. Ho muon noi cau hoi va nghe cau tra loi.

**Gia tri mang lai:**
- Tang toc do truy van len 5-10x so voi go ban phim trong moi truong xuong.
- Ho tro KTV nang cao it kinh nghiem go phim.

**Personas huong den:** Technician, Lead Tech (chu yeu trong xuong)

### Tinh nang can xay dung

| Tinh nang | Mo ta |
| :--- | :--- |
| Speech-to-Text (STT) | Chuyen giong noi tieng Viet cua KTV thanh text query |
| Text-to-Speech (TTS) | Doc to cau tra loi bang giong tong hop tieng Viet |
| Wake Word Detection | KTV noi "Oi Copilot" de bat microphone |
| Noise Cancellation | Loc tieng on xuong de nhan dien chinh xac |

### User Stories

**Story 1:**
> La KTV dang kiem tra xe, toi muon hoi "xe bao loi BMS_OVERHEAT xu ly the nao" bang giong noi de khong can dung tay, nhan duoc cau tra loi doc to.

**Story 2:**
> La KTV, khi nhan duoc canh bao CAUTION, toi muon he thong doc to canh bao an toan de toi co the nghe trong khi mat van nhin vao xe.

### Acceptance Criteria (Extension Contract)

| ID | Tieu chi nghiem thu |
| :--- | :--- |
| AC-P201.1 | STT nhan dien tieng Viet co dau voi WER (Word Error Rate) <= 10% trong moi truong xuong |
| AC-P201.2 | Latency STT + pipeline + TTS <= 3 giay |
| AC-P201.3 | Wake word "Oi Copilot" duoc phat hien voi precision >= 95% |
| AC-P201.4 | TTS doc ro cac thuat ngu ky thuat: BMS, LFP, PDI |
| AC-P201.5 | CAUTION banner duoc doc truoc tien, to hon, giong khac biet |
| AC-P201.6 | Voice module la plugin — Phase 1 core khong bi thay doi |

### Rang buoc quan trong

- Phase 1 pipeline hoan toan khong doi — Voice chi them vao/ra.
- STT output phai duoc dua qua Input Guardrails Phase 1 truoc khi vao pipeline.
- TTS phai ho tro giong Viet co dau chuan xac.

### Phuong an du phong

Neu STT accuracy < 10% WER khong dat duoc thi giu lai text input cho KTV, Voice la optional feature.

---

## P2-02: OCR Error Extractor

### Tong quan

**Van de giai quyet:**
KTV nhin thay man hinh xe bao loi nhu "P0301" nhung phai go tay lai vao chatbot, ton thoi gian va hay go nham.

**Gia tri mang lai:**
- KTV chup anh man hinh hien thi loi → he thong tu dong doc ma loi → tra cuu ngay.
- Giam thoi gian tra cuu tu 30 giay xuong con 5 giay.

### Tinh nang can xay dung

| Tinh nang | Mo ta |
| :--- | :--- |
| Camera Input | Cho phep KTV chup anh hoac upload screenshot man hinh xe |
| OCR Processing | Trich xuat text (dac biet ma DTC) tu anh |
| Error Code Recognition | Nhan dien ma loi trong text OCR (regex P\d+, E\d+, BMS_) |
| Auto-populate Chat | Tu dong dua ma loi vao chat box, trigger Error Lookup |

### User Stories

**Story 1:**
> La KTV, khi thay man hinh xe hien loi "BMS_OVERHEAT", toi muon chup anh man hinh va he thong tu dong nhan ra ma loi va tra cuu ngay cho toi.

### Acceptance Criteria (Extension Contract)

| ID | Tieu chi nghiem thu |
| :--- | :--- |
| AC-P202.1 | OCR doc chinh xac ma DTC tren man hinh xe voi accuracy >= 95% |
| AC-P202.2 | Ho tro anh chup tu camera dien thoai va screenshot upload |
| AC-P202.3 | Ma loi duoc nhan dien tu dong va dua vao Error Lookup pipeline |
| AC-P202.4 | Xu ly anh hoan thanh trong < 3 giay |
| AC-P202.5 | Khi OCR khong doc duoc → hien thi yeu cau nhap tay, khong loi 500 |

---

## P2-03: QR Code Vehicle Resolver

### Tong quan

**Van de giai quyet:**
Moi xe VinFast deu co tem QR. KTV phai nhap tay thong tin xe (model, VIN) khi hoi ve xe cu the.

**Gia tri mang lai:**
- Quet QR → tu dong nhan dien model xe, lich su bao duong → context hoa cau tra loi.

### Tinh nang can xay dung

| Tinh nang | Mo ta |
| :--- | :--- |
| QR Scanner | Quet ma QR tren tem xe |
| Vehicle Data Resolver | Map QR → model xe, VIN, nam san xuat |
| Context Injection | Tu dong them thong tin xe vao cau hoi de RAG chinh xac hon |

### User Stories

**Story 1:**
> La KTV, khi quet QR tren xe, he thong tu dong biet day la xe Klara S 2025 va tu dong them thong tin nay vao cau hoi cua toi de duoc tra loi chinh xac hon.

### Acceptance Criteria (Extension Contract)

| ID | Tieu chi nghiem thu |
| :--- | :--- |
| AC-P203.1 | QR scan thanh cong tren >= 95% cac tem xe VinFast chua bi mo |
| AC-P203.2 | Scan → resolve vehicle info trong < 1 giay |
| AC-P203.3 | Vehicle context duoc them vao AgentState, cai thien RAG accuracy |
| AC-P203.4 | QR bi mo/hu → hien thi form nhap tay, khong crash |

---

## P2-04: Image Understanding

### Tong quan

**Van de giai quyet:**
KTV gap su co nhin thay bang mat (day dien bi tu, linh kien bi chay) nhung kho mo ta bang text.

**Gia tri mang lai:**
- KTV chup anh su co → AI phan tich hinh anh → de xuat cach xu ly.

### Tinh nang can xay dung

| Tinh nang | Mo ta |
| :--- | :--- |
| Damage Detection | Nhan dien linh kien bi hong, chay, bi noi tu anh |
| Visual Error Matching | So sanh voi thu vien anh loi chuan cua VinFast |
| Repair Suggestion | De xuat buoc sua chua dua tren phan tich anh |

### Acceptance Criteria (Extension Contract)

| ID | Tieu chi nghiem thu |
| :--- | :--- |
| AC-P204.1 | Phan loai dung loai hong hoc (chay, mo, nut vu...) voi accuracy >= 80% |
| AC-P204.2 | Ke qua phan tich anh duoc ket hop voi Error Lookup cho cau tra loi day du |
| AC-P204.3 | Anh khong ro/khong lien quan → thong bao ro rang va yeu cau mo ta bang text |

### Rang buoc

- Can thu vien anh chuan ve hang hoa loi cua VinFast.
- Model multimodal phai ho tro tieng Viet tot.
- Chi deploy sau khi co du anh nhan hang de train/validate.

---

## P2-05: Advanced Memory

### Tong quan

**Van de giai quyet:**
Phase 1 chi luu ngay canh session. KTV phai nhac lai boi canh khi mo session moi.

**Gia tri mang lai:**
- He thong nho xe KTV thuong lam viec, loai loi hay gap, so thich tra loi → tu dong cung cap context.

### Tinh nang can xay dung

| Tinh nang | Mo ta |
| :--- | :--- |
| Long-term User Profile | Luu thong tin KTV: ten, vai tro, xe hay lam, loi hay gap |
| Cross-session Context | Nho cac cuoc tro chuyen truoc de tang do chinh xac |
| Personalized Suggestions | Goi y cau hoi dua tren lich su cua KTV cu the |

### Acceptance Criteria (Extension Contract)

| ID | Tieu chi nghiem thu |
| :--- | :--- |
| AC-P205.1 | He thong nho duoc top-5 ma loi KTV hay gap trong 30 ngay qua |
| AC-P205.2 | Context tu session truoc duoc inject vao query moi mot cach tu dong |
| AC-P205.3 | KTV co the xoa lich su ca nhan cua minh bat ky luc nao (GDPR-ready) |
| AC-P205.4 | Memory khong anh huong den Phase 1 Guardrails va RBAC |

---

## P2-06: Multi-Agent Orchestration

### Tong quan

**Van de giai quyet:**
Khi so luong skills tang len (> 8 skills), Orchestration Engine Phase 1 kho quan ly va dieu phoi.

**Gia tri mang lai:**
- Agent chuyen biet (Research Agent, Safety Agent, Ticket Agent) hop tac de xu ly cac vu phuc tap.

### Kien truc du kien

```
Orchestrator Agent (supervisor)
     |
     |-- Research Agent     (xu ly RAG, Error Lookup)
     |-- Safety Agent       (xu ly caution, guardrails)
     |-- Ticket Agent       (xu ly escalation)
     |-- [Future agents...] (co the them moi khong can refactor)
```

### Acceptance Criteria (Extension Contract)

| ID | Tieu chi nghiem thu |
| :--- | :--- |
| AC-P206.1 | Orchestrator phan cong dung task cho dung agent |
| AC-P206.2 | Agents giao tiep qua shared state, khong co direct dependency |
| AC-P206.3 | Phase 1 Skills khong bi thay doi — chinh la agents cua Phase 2 |
| AC-P206.4 | Neu mot agent fail → Orchestrator fallback sang Ticket Agent |

---

## P2-07: History-Augmented RAG

### Tong quan

**Van de giai quyet:**
RAG Phase 1 chi tim trong Knowledge Base tinh. Nhung co nhieu case tuong tu da duoc giai quyet truoc do.

**Gia tri mang lai:**
- RAG Phase 2 ket hop ca Knowledge Base + Lich su Ticket da dong cua → tang FCR len them 20%.

### Tinh nang can xay dung

| Tinh nang | Mo ta |
| :--- | :--- |
| Ticket Knowledge Base | Index hoa tat ca Ticket da dong vao kho du lieu rieng |
| History Search | Khi RAG khong tim duoc → search trong closed tickets |
| Solution Reuse | De xuat giai phap da dung thanh cong tu truoc |

### Acceptance Criteria (Extension Contract)

| ID | Tieu chi nghiem thu |
| :--- | :--- |
| AC-P207.1 | Closed ticket duoc index hoa sau 24h ke tu khi dong |
| AC-P207.2 | RAG co the tim trong ca Knowledge Base va Ticket History |
| AC-P207.3 | Solution de xuat tu lich su duoc gan nhan ro rang la "Giai phap tu truoc" |
| AC-P207.4 | PII trong Ticket duoc mask truoc khi index |

---

## P2-08: Dashboard & Analytics

### Tong quan

**Van de giai quyet:**
Hien tai khong co cach nao do luong hieu qua he thong, cac ma loi pho bien, hay cac KTV can ho tro them.

**Gia tri mang lai:**
- Service Manager va IT Admin co the theo doi KPIs he thong theo thoi gian thuc.
- Phat hien som cac diem yeu de cai thien.

### Cac dashboard can xay dung

**Dashboard 1 — IT Admin: System Health**

| Widget | Mo ta |
| :--- | :--- |
| Request Volume | So luong query theo gio/ngay/tuan |
| Intent Distribution | Phan bo WORKFLOW/RAG/ERROR/FORM (bieu do tron) |
| Guardrail Blocks | So lan va loai tan cong bi chan |
| Latency Percentiles | P50, P95, P99 latency theo thoi gian |
| Ticket Queue | So Ticket dang cho xu ly theo priority |

**Dashboard 2 — Service Manager: Business KPIs**

| Widget | Mo ta |
| :--- | :--- |
| AI Deflection Rate | % cau hoi AI tu xu ly (target >= 60%) |
| Top Error Codes | 10 ma loi duoc hoi nhieu nhat |
| Onboarding Completion | KTV moi hoan thanh onboarding checklist |
| RAG Accuracy Trend | Do tin cay RAG theo thoi gian |
| Hallucination Alerts | Cac truong hop co the hallucination |

### Acceptance Criteria (Extension Contract)

| ID | Tieu chi nghiem thu |
| :--- | :--- |
| AC-P208.1 | Dashboard tai trong < 3 giay voi 90 ngay du lieu |
| AC-P208.2 | Du lieu dashboard delay toi da 5 phut so voi thuc te |
| AC-P208.3 | IT Admin chi thay System Health dashboard |
| AC-P208.4 | Service Manager chi thay Business KPIs, khong thay du lieu ca nhan KTV |
| AC-P208.5 | Export CSV cho tat ca bieu do |

---

## P2-09: Sales/Pricing Module

### Tong quan

**Van de giai quyet:**
Nhan vien kinh doanh tai DLPP can tra cuu nhanh cau hinh xe, chinh sach gia, chuong trinh khuyen mai.

**Gia tri mang lai:**
- Sales staff co the tra loi khach hang nhanh hon, chinh xac hon ve cau hinh va gia xe.

**Luu y quan trong:**
Module nay phuc vu BOI PHOI KHAC (Sales, khong phai KTV). Can tao kho du lieu Knowledge Base rieng voi phan quyen rieng, khong merge voi Phase 1 data.

### Personas moi

| Persona | Quyen han |
| :--- | :--- |
| Sales Staff | Xem cau hinh xe, bang gia ban le, chuong trinh khuyen mai |
| Sales Manager | + Xem bao cao doanh so, so sanh DLPP |

### Acceptance Criteria (Extension Contract)

| ID | Tieu chi nghiem thu |
| :--- | :--- |
| AC-P209.1 | Sales Staff chi xem gia ban le, khong xem gia nhap cua DLPP |
| AC-P209.2 | Gia va cau hinh duoc cap nhat tu file Excel hang tuan |
| AC-P209.3 | Phase 1 KTV data hoan toan doc lap, khong bi o nhiem |
| AC-P209.4 | Sales module co Input Guardrails rieng, khong dung chung Phase 1 |

---

## P2-10: Manager Dashboard

### Tong quan

**Van de giai quyet:**
Service Manager hien tai khong co cong cu theo doi hieu suat KTV va chat luong xu ly xe.

**Gia tri mang lai:**
- Manager co the theo doi theo thoi gian thuc: xe nao dang xu ly, KTV nao can ho tro.

### Tinh nang can xay dung

| Tinh nang | Mo ta |
| :--- | :--- |
| KTV Performance Board | Thong ke cau hoi cua tung KTV, ty le tu giai quyet |
| Live Queue View | Danh sach Ticket dang xu ly theo priority |
| Knowledge Gap Detection | Phat hien chu de KTV hay gap kho khan |
| Alert System | Thong bao khi co Ticket urgent chua duoc xu ly > 30 phut |

### Acceptance Criteria (Extension Contract)

| ID | Tieu chi nghiem thu |
| :--- | :--- |
| AC-P210.1 | Dashboard chi hien thi du lieu DLPP cua Manager do, khong leak data DLPP khac |
| AC-P210.2 | Alert urgent Ticket duoc gui trong < 5 phut qua email hoac notification |
| AC-P210.3 | KTV Performance Board an danh theo tuy chon Manager |

---

## P2-11: Offline Mode (Web App nội bộ + AI cục bộ)

### Tong quan

**Van de giai quyet:**
Mot so DLPP o vung nong thon co ket noi internet khong on dinh. KTV khong the dung chatbot khi mat mang.

**Gia tri mang lai:**
- He thong van hoat dong co ban khi mat internet (Workflow + Error Lookup offline).

### Kien truc du kien

```
Web App hoỗ trợ chế độ offline
     |-- Bộ nhớ cục bộ: Lưu cache quy trình và bảng mã lỗi
     |-- AI cục bộ: Mô hình AI nhẹ hoạt động không cần internet
     |-- Đồng bộ: Tự động đồng bộ dữ liệu khi có lại kết nối
```

### Acceptance Criteria (Extension Contract)

| ID | Tieu chi nghiem thu |
| :--- | :--- |
| AC-P211.1 | Workflow Skill va Error Lookup hoat dong offline (tu cache) |
| AC-P211.2 | RAG Policy Copilot offline voi Local LLM nhe (giam chat luong chap nhan duoc) |
| AC-P211.3 | Du lieu dong bo tu dong khi co lai ket noi |
| AC-P211.4 | Nguoi dung biet ro khi dang o che do offline (banner thong bao) |

### Rang buoc

- AI cục bộ (chế độ offline) sẽ kém chính xác hơn AI Service trên cloud (chấp nhận được cho Offline).
- Offline mode chi ho tro 2 skill (Workflow, Error Lookup), khong ho tro RAG day du.

---

## P2-12: Voice Cloning

### Tong quan

**Van de giai quyet:**
TTS Phase 2-01 dung giong tong hop chung. DLPP muon he thong noi bang giong cua Truong phong hoac nguoi duoc ho tin tuong hon.

**Gia tri mang lai:**
- Truc nghiem ho tro "quen thuoc" hon, tang su tin tuong cua KTV vao cau tra loi.

### Acceptance Criteria (Extension Contract)

| ID | Tieu chi nghiem thu |
| :--- | :--- |
| AC-P212.1 | Clone giong tu 10 phut audio mau cua nguoi duoc chon |
| AC-P212.2 | Giong clone phat am dung cac thuat ngu ky thuat: BMS, LFP, PDI |
| AC-P212.3 | Co cho phep tat Voice Cloning, quay ve giong mac dinh |
| AC-P212.4 | Khong su dung audio giong noi de train cac model ben ngoai (privacy) |

---

## Phan tich Dependency Phase 2

```
P2-01 Voice AI
     |-- Phu thuoc: Phase 1 on dinh
     |-- Block: Khong co gi

P2-02 OCR
     |-- Phu thuoc: Phase 1 on dinh, co du lieu anh
     |-- Block: Khong co gi

P2-05 Advanced Memory
     |-- Phu thuoc: Phase 1 on dinh, du du lieu session
     |-- Block: Khong co gi

P2-07 History-Augmented RAG
     |-- Phu thuoc: P2-05 Advanced Memory (can co Ticket History index)
     |-- Block: Phai lam P2-05 truoc

P2-06 Multi-Agent
     |-- Phu thuoc: Khi co >= 8 skills va can scale
     |-- Block: Khong can lam som

P2-08 Dashboard
     |-- Phu thuoc: >= 30 ngay van hanh Phase 1
     |-- Block: Can du lieu, lam sau

P2-09 Sales Module
     |-- Phu thuoc: Bo phan Sales yeu cau
     |-- Block: Khong can lam som

P2-10 Manager Dashboard
     |-- Phu thuoc: P2-08 Dashboard (dung chung infra)
     |-- Block: Lam sau P2-08

P2-11 Offline Mode
     |-- Phu thuoc: Phase 1 on dinh
     |-- Block: Chi lam khi co DLPP cu the yeu cau

P2-12 Voice Cloning
     |-- Phu thuoc: P2-01 Voice AI
     |-- Block: Lam sau P2-01
```

---

## Goi y Thu tu Implementation Phase 2

**Luot 1 (Thang 2-3 sau MVP go-live) — High Value, Low Risk:**

| Thu tu | Module | Ly do uu tien |
| :--- | :--- | :--- |
| 1 | P2-08 Dashboard & Analytics | Can du lieu san sang ngay sau 30 ngay |
| 2 | P2-01 Voice AI | Nhu cau cao tu KTV trong xuong |
| 3 | P2-02 OCR Error Extractor | Giam loi nhap, tang toc do KTV |

**Luot 2 (Thang 4-5 sau MVP go-live) — Medium Value:**

| Thu tu | Module | Ly do uu tien |
| :--- | :--- | :--- |
| 4 | P2-07 History-Augmented RAG | Tang FCR sau khi co du Ticket data |
| 5 | P2-05 Advanced Memory | Phu thuoc vao enough session data |
| 6 | P2-10 Manager Dashboard | Sau khi P2-08 infrastructure san sang |

**Luot 3 (Thang 6+ sau MVP go-live) — Strategic / On-demand:**

| Thu tu | Module | Ly do uu tien |
| :--- | :--- | :--- |
| 7 | P2-09 Sales Module | Khi Sales request cu the |
| 8 | P2-03 QR Code | Khi DLPP co quyet dinh su dung QR scanner |
| 9 | P2-11 Offline Mode | Chi khi co DLPP vung sau yeu cau |
| 10 | P2-04 Image Understanding | Sau khi co du thu vien anh loi |
| 11 | P2-06 Multi-Agent | Khi so luong skill > 8 |
| 12 | P2-12 Voice Cloning | Sau khi P2-01 on dinh |

---

## Ma tran Rui ro Phase 2

| ID | Rui ro | Likelihood | Impact | Muc do | Bien phap |
| :--- | :--- | :---: | :---: | :---: | :--- |
| R2-01 | Voice AI accuracy kem trong moi truong xuong on ao | Cao | Trung binh | CAO | Test tai DLPP thuc te truoc khi deploy rong, giu lai fallback text |
| R2-02 | OCR khong doc duoc man hinh xe doi cu (do de) | Trung binh | Trung binh | TRUNG BINH | Test voi nhieu loai man hinh, fallback sang nhap tay |
| R2-03 | Local LLM Offline kem chinh xac lam KTV mat tin tuong | Trung binh | Cao | CAO | Giai thich ro "Offline Mode - ket qua co the kem chinh xac" |
| R2-04 | Dashboard bi lo du lieu ca nhan KTV | Thap | Cao | CAO | RBAC tiet lo du lieu ca nhan, audit truoc khi release |
| R2-05 | Sales Module lam phong Phase 1 Guardrails | Thap | Cao | CAO | Collections va Guardrails hoan toan doc lap |
| R2-06 | Voice Cloning bi lam dung (gia mao giong noi) | Thap | Cao | CAO | Chi cho phep IT Admin upload audio mau, ghi log moi session |

---

## Nguyen tac Kien truc cho Phase 2

De dam bao Phase 1 khong bi ton hai khi them Phase 2:

1. **Plugin Architecture:** Moi Phase 2 module la mot plugin doc lap. Khong sua code Phase 1.
2. **Separate Knowledge Base:** Phase 2 data (Sales, Manager) phai o kho du lieu Knowledge Base rieng.
3. **Separate Guardrails:** Module moi co the co Guardrails rieng, khong merge voi Phase 1.
4. **Interface First:** Phase 2 module tuan theo chuan giao dien Skill da dinh nghia trong Phase 1.
5. **Feature Flags:** Moi Phase 2 module co the bat/tat qua config flag, khong can deploy lai.

---

## Dinh nghia Extension Contract

Moi module Phase 2 trong tai lieu nay duoc coi la "Extension Contract" nghia la:

- **Xac dinh ro WHAT:** Tinh nang can lam gi, de lam gi (da mo ta o tren).
- **Xac dinh Acceptance Criteria:** Tieu chi de biet da lam xong.
- **CHUA xac dinh HOW:** Chi tiet implement se duoc viet trong SDD Phase 2 khi bat dau thuc hien.
- **CHUA co timeline:** Timeline se duoc set sau khi Phase 1 on dinh va co yeu cau cu the.

Khi bat dau implement bat ky module Phase 2 nao, PM phai:
1. Xac nhan Go/No-Go criteria da dat.
2. Yeu cau Tech Lead viet SDD chi tiet cho module do.
3. PO viet User Stories va AC day du.
4. Moi chay sprint Phase 2.

---

*MVP Specification Phase 2 v1.0 — VF-Onboarding Copilot — Team T223*
*Tai lieu Extension Contract cho Phase 2 — chi implement sau khi Phase 1 on dinh >= 30 ngay.*
*PM su dung tai lieu nay cho long-term planning va stakeholder communication.*
