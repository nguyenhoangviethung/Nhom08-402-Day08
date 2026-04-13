# Báo Cáo Nhóm: Lab 08 — Full RAG Pipeline

**Nhóm:** Nhóm 08 - Lớp E402
**Hệ thống:** Trợ lý Nội bộ khối CS & IT Helpdesk (Internal AI Assistant)
**Ngày nộp:** 12/04/2026

---

## 1. Phân công nhiệm vụ (Team Roles)

Nhóm 08 đã phân bổ công việc linh hoạt, mỗi thành viên đảm nhận các file cụ thể chéo nhau giữa các vai trò (Tech, Eval, Doc) để đảm bảo hiểu sâu toàn bộ Pipeline:

| Thành viên | Phân vai (Roles) | Trách nhiệm & File thực hiện (Đóng góp chính) |
| :--- | :--- | :--- |
| **Hoàng** | Tech Lead / Eval Owner | Phát triển luồng Indexing (`index.py`) và chuẩn bị dữ liệu kiểm thử (`data/test_questions.json`). |
| **Hưng** | Tech Lead / Eval Owner | Đồng phát triển `index.py`, xây dựng script đánh giá (`eval.py`) và chấm điểm `results/scorecard_baseline.md`. |
| **Hồng Anh** | Tech Lead | Chịu trách nhiệm chính phát triển lõi hệ thống RAG, luồng truy xuất và sinh câu trả lời (`rag_answer.py`). |
| **Hùng** | Tech Lead / Doc Owner | Xây dựng script `eval.py`, chịu trách nhiệm chạy file log Giờ G (`logs/grading_run.json`) và ghi nhận `docs/tuning-log.md`. |
| **Giang** | Eval Owner / Doc Owner | Thực hiện đánh giá `results/scorecard_baseline.md`, thiết kế tài liệu `docs/architecture.md` và tổng hợp `reports/group_report.md`. |
| **Bình** | Eval Owner / Doc Owner | Thực hiện đánh giá cấu hình Variant (`results/scorecard_variant.md`), ghi nhận A/B testing (`docs/tuning-log.md`) và viết `reports/group_report.md`. |

---

## 2. Quy trình thực hiện (Sprints)

### Sprint 1: Xây dựng cơ sở dữ liệu (Indexing)
* **Chiến lược:** Sử dụng `RecursiveCharacterTextSplitter`.
* **Thông số:** `chunk_size=200`, `overlap=50`.
* **Metadata:** Mỗi chunk được đính kèm: `source`, `section`, `effective_date`, `department`.
* **Lý do:** Đảm bảo các quy trình nghiệp vụ dài không bị chặt đứt, đồng thời Metadata đầy đủ giúp hệ thống thực hiện Hard-filter và trích dẫn nguồn (Citation) chính xác.

### Sprint 2: Baseline Pipeline (Dense Search)
* **Luồng hoạt động:** Sử dụng Vector Search thuần túy để lấy Top-k=3 liên quan nhất.
* **Generator:** Sử dụng `GPT-4a` với `temperature=0` để loại bỏ sự ngẫu nhiên.
* **Prompting:** Thiết lập quy tắc "thiết quân luật" buộc AI từ chối trả lời (Abstain) nếu không tìm thấy dữ liệu trong Context.

### Sprint 3: Tuning & Tối ưu hóa (Variant)
* **Cải tiến:** Nhóm triển khai cấu hình **Dense Search + Cross-Encoder Reranker**.
* **Quy trình:** Mở rộng không gian tìm kiếm lên Top-15, sau đó dùng mô hình `ms-marco-MiniLM-L-6-v2` để chấm điểm lại sự liên quan.
* **Lý do:** Chiến thuật này giúp giải quyết các câu hỏi "Multi-hop" (như `gq06`) nơi thông tin cần trích xuất nằm rải rác ở nhiều tài liệu khác nhau mà Vector Search thông thường dễ bỏ sót.

### Sprint 4: Đánh giá & Hoàn thiện
* **Kiểm thử:** Chạy 10 câu hỏi Grading ẩn của giảng viên.
* **Evaluation:** Sử dụng scorecard để đối chiếu Baseline và Variant, qua đó xác nhận độ hiệu quả của module Rerank.

---

## 3. Kiến trúc hệ thống (Architecture Diagram)

Hệ thống được thiết kế theo mô hình RAG tiêu chuẩn với module Rerank bổ trợ để tăng độ chính xác:



---

## 4. Kết quả đánh giá (Evaluation Summary)

Dựa trên kết quả thực tế từ `eval.py` và `logs/grading_run.json`:

| Metric (Metric) | Baseline (Dense) | Variant (Rerank) | Cải thiện (Delta) |
|:---|:---:|:---:|:---:|
| **Tổng điểm đạt được** | ../98 | **.../98** | **+...** |
| **Context Recall** | 70% | 90% | +20% |
| **Faithfulness (Độ trung thực)** | 100% | 100% | 0 |
| **Tỷ lệ Abstain (gq07)** | 1/1 | 1/1 | 0 |

**Nhận xét:** Cấu hình Variant (Rerank) cho thấy sự vượt trội ở các câu hỏi phức tạp. Mặc dù thời gian phản hồi chậm hơn 0.5s so với Baseline, nhưng độ chính xác trong việc chọn lọc ngữ cảnh đã giúp điểm số tổng quát tăng đáng kể.

---

## 5. Phân tích lỗi & Khắc phục (Failure Analysis)

* **Lỗi gặp phải:** Câu hỏi `gq04` (về % hoàn tiền) ở bản Baseline đôi khi lấy nhầm con số ở các điều khoản cũ.
* **Nguyên nhân:** Do các phiên bản chính sách có từ ngữ tương đồng cao, khiến Vector Search bị nhiễu.
* **Khắc phục:** Nhóm đã sử dụng Metadata `effective_date` để lọc lấy bản `v4` mới nhất trước khi thực hiện Search, giúp kết quả luôn đảm bảo tính thời sự (Freshness).

---

## 6. Kết luận & Đề xuất cải tiến

### Kết luận
Nhóm 08 đã hoàn thành đầy đủ 4 Sprint, xây dựng thành công một RAG Pipeline an toàn, có khả năng tự chắt lọc thông tin và từ chối bịa đặt. Việc áp dụng Reranker là quyết định kỹ thuật đúng đắn nhất để xử lý bộ dữ liệu đa dạng của IT Helpdesk.

### Đề xuất cải tiến (Future Works)
1.  **Hybrid Search:** Tích hợp thêm BM25 để bắt các keyword đặc thù (mã lỗi ERR, mã ticket) tốt hơn.
2.  **Parent-Document Retrieval:** Lưu trữ chunk nhỏ để search nhưng trả về chunk lớn cho LLM để tối ưu hóa ngữ cảnh.
3.  **Persist Store:** Chuyển sang lưu trữ ổ cứng thay vì RAM để hệ thống có tính ổn định lâu dài.