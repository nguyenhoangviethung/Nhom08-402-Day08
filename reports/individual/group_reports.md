# Báo Cáo Nhóm — Lab Day 08: Full RAG Pipeline

**Tên nhóm:** Nhóm 08 - Lớp E402  
**Thành viên:**
| Tên | Vai trò | Email |
|-----|---------|-------|
| Hoàng | Tech Lead / Eval Owner | hoangmai04222@gmail.com |
| Hưng | Tech Lead / Eval Owner | hoangduchung0311@gmail.com |
| Hồng Anh | Tech Lead | anh.anhle2004@gmail.com |
| Hùng | Tech Lead / Doc Owner | nguyenhoangviethung@gmail.com |
| Giang | Eval Owner / Doc Owner | nguyenhuonggiang06092004@gmail.com |
| Bình | Eval Owner / Doc Owner | binhntph50046@gmail.com |

**Ngày nộp:** 13/04/2026  
**Repo:** https://github.com/nguyenhoangviethung/Nhom08-402-Day08.git

---
## 1. Pipeline nhóm đã xây dựng

Hệ thống RAG của Nhóm 08 được tối ưu hóa để đóng vai trò Trợ lý Nội bộ cho khối CS & IT Helpdesk.

**Chunking:**
tách văn bản dựa trên cấu trúc tự nhiên (Heading-based) sau đó chia nhỏ theo đoạn văn với thông số **chunk_size=200** và **overlap=50**. Quyết định chọn chunk size nhỏ giúp trích xuất chính xác các điều khoản hẹp. Mỗi chunk được đính kèm metadata chi tiết (`source`, `section`, `department`, `effective_date`, `access`) nhằm đảm bảo ngữ cảnh không bị đứt đoạn và hỗ trợ trích dẫn nguồn (citation) một cách minh bạch.

**Embedding model:**
Hệ thống sử dụng mô hình local `bkai-foundation-models/vietnamese-bi-encoder`. Đây là mô hình nhúng tiếng Việt tối ưu cho phép bắt dính các ngữ nghĩa chuyên môn của nội quy công ty.

**Retrieval variant (Sprint 3):**
Nhóm chọn cấu hình **Dense Search + Reranker (Cross-Encoder)** (`use_rerank=True`). Thay vì chỉ lấy Top-3 từ Vector DB, hệ thống lấy Top-10 ứng viên (Candidates), sau đó dùng mô hình Reranker để chấm điểm lại mức độ liên quan trực tiếp giữa câu hỏi và từng chunk, rồi mới chọn ra Top-3 tốt nhất đưa vào LLM.

---

## 2. Quyết định kỹ thuật quan trọng nhất (200–250 từ)

**Quyết định:** Áp dụng mô hình Reranker ở giai đoạn Retrieval (Sprint 3) thay vì chỉ dùng Dense Search thông thường.

**Bối cảnh vấn đề:**
Trong giai đoạn chạy Baseline (Dense Search thuần túy), nhóm nhận thấy thuật toán Bi-Encoder tính toán khoảng cách vector rất nhanh nhưng đôi khi độ chính xác ngữ nghĩa bị hạn chế. Ví dụ ở câu `q08`, Baseline kéo được chunk nhưng LLM trả lời thiếu chi tiết (Completeness = 4/5) do chunk quan trọng nhất không được xếp ở vị trí số 1. Nhóm cần một cơ chế tinh chỉnh thứ hạng (fine-grained ranking) hiệu quả hơn.

**Các phương án đã cân nhắc:**

| Phương án | Ưu điểm | Nhược điểm |
|-----------|---------|-----------|
| **Query Expansion** | Xử lý tốt từ đồng nghĩa, cấu hình nhẹ, phản hồi nhanh. | Dễ sinh nhiễu (noise) nếu LLM mở rộng câu hỏi đi chệch hướng. |
| **Cross-Encoder Reranker** | Độ chính xác xếp hạng cao do mô hình đối chiếu trực tiếp (Cross-attention) giữa Query và Document. | Tăng độ trễ (latency) của hệ thống vì phải chạy qua một mô hình thứ hai. |

**Phương án đã chọn và lý do:**
Nhóm quyết định chọn **Reranker**. Đối với trợ lý nội bộ IT Helpdesk, tính chính xác của tài liệu được đưa lên hàng đầu, có thể đánh đổi bằng một chút độ trễ.

**Bằng chứng từ scorecard/tuning-log:**
Kết quả thực tế từ Scorecard cho thấy chiến lược này giúp tăng điểm Completeness ở câu `q08` (từ 4 lên 5) do lấy được ngữ cảnh đầy đủ hơn. Tuy nhiên, nó cũng bộc lộ nhược điểm làm giảm điểm Faithfulness tổng thể.

## 3. Kết quả grading questions 

Sau khi chạy pipeline với dữ liệu grading ẩn:

**Ước tính điểm raw:** ~68 / 98 (Bị phạt điểm do lỗi ảo giác ở q09, q10).

**Câu tốt nhất:** ID: **q02, q03, q04, q05** — Lý do: Hệ thống đạt điểm tuyệt đối (5/5/5/5). Dense retrieval bắt cực chuẩn xác tài liệu, và LLM tóm tắt hoàn hảo các điều kiện hoàn tiền, Flash Sale và số lượng thiết bị VPN.

**Câu fail:** ID: **q09** — Root cause: **Generation**. Câu hỏi không có thông tin trong tài liệu (Insufficient Context). Hệ thống abstain đúng khi trả lời "Tôi không biết", nhưng LLM lại không đưa ra được hướng dẫn liên hệ IT Helpdesk theo chuẩn mực của trợ lý ảo, dẫn đến điểm Completeness và Relevance = 1.

**Câu gq07 (abstain):** Ở cấu hình Hybrid, hệ thống xử lý **Tốt hơn Baseline** (Faithfulness tăng từ 3 lên 5). 

---
## 4. A/B Comparison — Baseline vs Variant 

Dựa vào `docs/tuning-log.md`, nhóm so sánh Baseline với Variant 2 (Hybrid Search) - biến thể tạo ra sự thay đổi rõ rệt nhất:

**Biến đã thay đổi:** Chuyển `retrieval_mode` từ "dense" sang "hybrid".
| Metric           | Baseline | Variant  | Delta |
| ---------------- | -------- | --------- | ------------------- |
| Faithfulness     | 4.30     | 4.30      | ~0               |
| Answer Relevance | 4.20     | 4.20      | ~0              |
| Context Recall   | 5.00     | 5.00      | ~0                |
| Completeness     | 3.40     | 3.40      | ~0               |

**Kết luận:**: Không có cải thiện đo được. Query Expansion không tạo ra delta trên bất kỳ metric nào.

**Lý do:** Corpus nhỏ (29 chunks, 5 tài liệu). Dense retrieval với `bkai-foundation-models/vietnamese-bi-encoder` đã đạt Context Recall 5.00/5 ngay từ baseline — tức là đã tìm đúng source cho tất cả câu hỏi có expected source. Expansion thêm query không mang lại chunk mới có giá trị.

---
## 5. Phân công và đánh giá nhóm
| Thành viên | Phần đã làm | Sprint
| :--- | :--- | :--- |
<<<<<<< HEAD
| **Hoàng** | Tech Lead / Eval Owner | Phát triển luồng Indexing (`index.py`) và chuẩn bị dữ liệu kiểm thử (`data/test_questions.json`). |
| **Hưng** | Tech Lead / Eval Owner | Đồng phát triển `index.py`, xây dựng script đánh giá (`eval.py`) và chấm điểm `results/scorecard_baseline.md`,`results/scorecard_variant.md`, `group_reports.md` |
| **Hồng Anh** | Tech Lead | Chịu trách nhiệm chính phát triển lõi hệ thống RAG, luồng truy xuất và sinh câu trả lời (`rag_answer.py`). |
| **Hùng** | Tech Lead / Doc Owner | Xây dựng script `eval.py`, chịu trách nhiệm chạy file log Giờ G (`logs/grading_run.json`) và ghi nhận `docs/tuning-log.md`. |
| **Giang** | Eval Owner / Doc Owner | Thực hiện đánh giá `results/scorecard_baseline.md`, thiết kế tài liệu `docs/architecture.md` và tổng hợp `reports/group_report.md`. |
| **Bình** | Eval Owner / Doc Owner | Thực hiện đánh giá cấu hình Variant (`results/scorecard_variant.md`), ghi nhận A/B testing (`docs/tuning-log.md`) và viết `reports/group_report.md`. |
=======
| **Hoàng** |Phát triển luồng Indexing (`index.py`) và chuẩn bị dữ liệu kiểm thử (`data/test_questions.json`). |  1  |
| **Hưng** | Đồng phát triển `index.py`, xây dựng script đánh giá (`eval.py`) và chấm điểm `results/scorecard_baseline.md`. |   1, 4      |
| **Hồng Anh** | Chịu trách nhiệm chính phát triển lõi hệ thống RAG, luồng truy xuất và sinh câu trả lời (`rag_answer.py`). |   2, 3     |
| **Hùng** | Xây dựng script `eval.py`, chịu trách nhiệm chạy file log Giờ G (`logs/grading_run.json`) và ghi nhận `docs/tuning-log.md`. |  4     |
| **Giang** | Thực hiện đánh giá `results/scorecard_baseline.md`, thiết kế tài liệu `docs/architecture.md` và tổng hợp `reports/group_report.md`. |    4    |
| **Bình** | Thực hiện đánh giá cấu hình Variant (`results/scorecard_variant.md`), ghi nhận A/B testing (`docs/tuning-log.md`) và viết `reports/group_report.md`. |      4     |

**Điều nhóm làm tốt:**
Việc chọn mô hình `vietnamese-bi-encoder` giúp Context Recall luôn đạt 100%. Quá trình Tuning (chạy 2 Variant) được ghi nhận log bài bản, phân lập rõ ràng nguyên nhân lỗi.

**Điều nhóm làm chưa tốt:**
Nút thắt lớn nằm ở khâu Generation nhưng nhóm lại mất nhiều thời gian loay hoay sửa ở khâu Retrieval (Transform/Hybrid). 
>>>>>>> afa8ac38fa5f2d86758138fcdfb8beb3a3138656

---

## 6. Nếu có thêm 1 ngày, nhóm sẽ làm gì? 

Dựa trên kết luận từ Tuning Log, nhóm sẽ triển khai **Reranking (Cross-Encoder: BAAI/bge-reranker-v2-m3)**.
Vì Context Recall đã đạt max (5.0), việc cần làm không phải là tìm *thêm* tài liệu, mà là *sắp xếp* lại tài liệu. Reranker sẽ giúp đẩy đúng chunk có chứa điểm mấu chốt (như escalation 10 phút ở q06) lên vị trí số 1, từ đó cải thiện Completeness. Song song đó, nhóm sẽ siết chặt Grounded Prompt để trị dứt điểm lỗi bịa đặt.

