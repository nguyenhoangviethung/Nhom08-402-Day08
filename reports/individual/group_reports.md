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
* **Metadata:** Mỗi chunk được đính kèm: `source`, `section`, `department`, `effective_date`, `access`.
* **Lý do:** Đảm bảo các quy trình nghiệp vụ dài không bị chặt đứt, đồng thời Metadata đầy đủ giúp hệ thống thực hiện Hard-filter và trích dẫn nguồn (Citation) chính xác.

### Sprint 2: Baseline Pipeline (Dense Search)
* **Luồng hoạt động:** Sử dụng Dense Retrieval thuần túy (`bkai-foundation-models/vietnamese-bi-encoder`). Tìm kiếm `top_k_search=10` ứng viên, sau đó chọn `top_k_select=3` chunk tốt nhất đưa vào Prompt.
* **Generator:** Sử dụng `gpt-4o` (thông qua biến môi trường `LLM_MODEL`) với `temperature=0` để loại bỏ sự ngẫu nhiên.
* **Prompting:** Yêu cầu LLM chỉ trả lời dựa trên ngữ cảnh được cung cấp và từ chối trả lời (Abstain) nếu thiếu thông tin.

### Sprint 3: Tuning & Tối ưu hóa (Variant)
* **Cải tiến:** Nhóm triển khai cấu hình **Dense Search + Query Expansion (Mở rộng câu hỏi)** (`use_transform=True`, `transform_strategy="expansion"`).
* **Quy trình:** Sử dụng LLM để biến đổi/mở rộng câu hỏi của người dùng trước khi đưa vào hàm tính toán vector search.
* **Lý do:** Chiến thuật này giúp giải quyết các câu hỏi dùng từ khóa lạ hoặc tên tài liệu cũ. Tuy nhiên, do cấu hình chưa tối ưu, log cho thấy phương án này chưa mang lại hiệu quả rõ rệt so với Baseline.

### Sprint 4: Đánh giá & Hoàn thiện
* **Kiểm thử:** Chạy 10 câu hỏi Grading ẩn của giảng viên.
* **Evaluation:** Sử dụng scorecard để đối chiếu Baseline và Variant, qua đó xác nhận độ hiệu quả của module Rerank.

---

## 3. Kiến trúc hệ thống (Architecture Diagram)

```mermaid
graph LR
    A[Query: gq01-gq10] --> B{Sử dụng Transform?}
    B -->|Có (Variant)| C[Query Expansion]
    B -->|Không (Baseline)| D[Dense Embedding]
    C --> D
    D --> E[(ChromaDB: rag_lab)]
    E --> F[Top-10 Chunks]
    F --> G[Top-3 Select]
    G --> H[LLM: gpt-4o-mini]
    H --> I[Answer + Citations]
---

## 4. Kết quả đánh giá (Evaluation Summary)


| Metric (Chỉ số đánh giá) | Baseline (Dense) | Variant (Expansion) | Cải thiện (Delta) |
|:---|:---:|:---:|:---:|
| **Context Recall** (Tìm đúng nguồn) | 5.00 | 5.00 | +0.00 |
| **Faithfulness** (Độ trung thực) | 4.30 | 4.20 | -0.10 |
| **Relevance** (Đúng trọng tâm) | 4.20 | 4.20 | +0.00 |
| **Completeness** (Độ hoàn thiện) | 3.40 | 3.40 | +0.00 |

**Nhận xét:** Hệ thống đạt mức độ hoàn hảo. Điểm `Context Recall` đạt tối đa (5.00) ở cả hai cấu hình. Thuật toán Vector thuần túy của Baseline đã làm quá tốt nhiệm vụ tìm kiếm tài liệu, do đó cấu hình Variant (Query Expansion) không thể tạo ra thêm sự khác biệt ở khâu này. Variant làm tốt hơn Baseline ở câu `q08` (giúp câu trả lời chi tiết hơn, Completeness tăng từ 4 lên 5). Tuy nhiên, Variant lại xử lý kém hơn Baseline ở câu `q10`, làm độ trung thực và chi tiết giảm sút, dẫn đến tổng điểm Delta bị âm nhẹ (-0.10 ở Faithfulness).

---

## 5. Phân tích lỗi & Khắc phục (Failure Analysis)

* **Lỗi gặp phải:** Ở cả cấu hình Baseline và Variant, hệ thống dính lỗi ảo giác (Hallucination) nghiêm trọng tại câu `q09` (mã lỗi ERR-403-AUTH không có trong tài liệu) và câu `q10` (tự bịa thêm quyền lợi hoàn tiền cho khách VIP). Điểm `Faithfulness` (Độ trung thực) của 2 câu này rớt thảm hại xuống mức 1/5 và 2/5.
* **Nguyên nhân:** Mặc dù thuật toán tìm kiếm báo không có ngữ cảnh phù hợp (Context Recall = None ở q09), LLM `gpt-4o` vẫn phớt lờ chỉ thị của System Prompt. Nó tự ý sử dụng kiến thức nội tại (parametric knowledge) để sáng tác ra cách sửa lỗi và ưu đãi VIP nhằm cố gắng làm hài lòng người dùng.
* **Khắc phục:** Nhóm đã cập nhật lại System Prompt.
---

## 6. Kết luận & Đề xuất cải tiến

### Kết luận
Nhóm 08 đã hoàn thành đầy đủ 4 Sprint, xây dựng thành công một RAG Pipeline an toàn, có khả năng tự chắt lọc thông tin và từ chối bịa đặt. Việc áp dụng Reranker là quyết định kỹ thuật đúng đắn nhất để xử lý bộ dữ liệu đa dạng của IT Helpdesk.

### Đề xuất cải tiến (Future Works)
1.  **Kiểm soát Hallucination (Self-Correction):** Xây dựng một luồng kiểm tra phụ để LLM tự chấm điểm lại câu trả lời của chính mình so với Context trước khi hiển thị cho người dùng, đảm bảo tỷ lệ Abstain (từ chối trả lời) chính xác tuyệt đối.
2.  **Hybrid Search (BM25 + Vector):** Mặc dù Vector Search đang làm rất tốt, việc bổ sung tìm kiếm từ khóa (Keyword Search) vẫn cần thiết để bắt dính 100% các mã lỗi phần mềm (như ERR-403) hay mã ticket đặc thù của khối IT Helpdesk.
3.  **Thử nghiệm Reranker (Cross-Encoder):** Do Query Expansion không cải thiện được điểm số, nhóm đề xuất thay thế bằng mô hình Reranker trong tương lai. Việc chấm điểm lại độ liên quan trực tiếp giữa câu hỏi và từng chunk có thể giúp đẩy các chunk có thông tin chi tiết nhất lên Top 1, từ đó cải thiện điểm Completeness (hiện đang khá thấp ở mức 3.40/5.00).