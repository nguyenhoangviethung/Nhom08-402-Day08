# Scorecard: Baseline Pipeline (Dense Retrieval)

**Thời gian đánh giá:** [15h:30, 12/04/2026]
**Cấu hình Baseline:** `retrieval_mode="dense"`, `top_k=3`, `LLM=OpenAI 4o`

## Tổng quan kết quả (Baseline)
- **Tổng điểm raw:** 60/98
- **Điểm quy đổi (Hệ 30):** 18.37 / 30
- **Số câu lấy đúng nguồn (Context Recall):** 10/10 câu.
- **Số câu bị Hallucination (Penalty):** 2 câu.

## Chi tiết đánh giá 10 câu Test (Baseline)

*(Thang điểm đánh giá: F = Faithfulness, R = Relevance, Rc = Context Recall, C = Completeness. Tối đa 5 điểm/tiêu chí).*

| ID | Câu hỏi tóm tắt | Điểm F/R/Rc/C | Faithfulness | Nhận xét chi tiết (Dựa trên Log) |
|:---|:---|:---|:---:|:---|
| **q01** | SLA xử lý ticket P1 | 5 / 5 / 5 / 3 | Pass | Nguồn chuẩn (Rc=5), không bịa (F=5). Tuy nhiên câu trả lời hơi thiếu chi tiết (C=3). |
| **q02** | Thời gian hoàn tiền | 5 / 5 / 5 / 5 | Pass | Trả lời hoàn hảo, đầy đủ ý. |
| **q03** | Phê duyệt quyền Level 3 | 5 / 5 / 5 / 5 |  Pass | Trả lời hoàn hảo, chính xác. |
| **q04** | Hoàn tiền SP kỹ thuật số | 5 / 5 / 5 / 5 |  Pass | Trả lời hoàn hảo, bắt đúng ngoại lệ. |
| **q05** | Số lần đăng nhập sai | 5 / 5 / 5 / 5 |  Pass | Trả lời hoàn hảo, chính xác. |
| **q06** | Escalation P1 | 5 / 5 / 5 / 2 |  Pass | Hệ thống lấy đúng nguồn nhưng câu trả lời quá vắn tắt, thiếu hụt thông tin quan trọng (C=2). |
| **q07** | Approval Matrix (Alias) | 5 / 5 / 5 / 2 |  Pass | **Điểm sáng:** Baseline nhận diện được tên tài liệu cũ (Alias) hoàn hảo (Rc=5). Nhưng câu trả lời vẫn chưa đủ chi tiết (C=2). |
| **q08** | Số ngày làm Remote | 5 / 5 / 5 / 4 |  Pass | Thông tin đầy đủ, gần đạt mức tối đa. |
| **q09** | Mã lỗi ERR-403-AUTH | 1 / 1 / None / 1 |  **FAIL** | **Cảnh báo Hallucination:** Điểm Faithfulness = 1. Hệ thống không tìm thấy nguồn (Rc=None) nhưng tự ý bịa ra câu trả lời thay vì Abstain. |
| **q10** | Hoàn tiền khách VIP | 2 / 1 / 5 / 2 |  **FAIL** | **Cảnh báo Hallucination:** Điểm Faithfulness = 2. Kéo đúng nguồn (Rc=5) nhưng tự bịa thêm quyền lợi cho khách VIP không có trong văn bản. |


**1. Điểm sáng của cấu hình Baseline (Dense Search):**
Khả năng truy xuất (Context Recall) đạt mức hoàn hảo (5.0/5.0). Mô hình `vietnamese-bi-encoder` hoạt động cực kỳ xuất sắc, bắt dính mọi tài liệu kể cả khi người dùng sử dụng tên gọi cũ của tài liệu (như câu q07).


**2. Điểm yếu / Failure Modes (Tại sao cần Variant?):**
- **Lỗ hổng Prompting (Hallucination):** Ở câu q09 và q10, hệ thống đã thất bại trong việc kiểm soát tính trung thực. Mặc dù system prompt có thể đã nhắc "Không trả lời nếu không có dữ liệu", LLM vẫn tự dùng kiến thức nội tại để giải thích lỗi 403 hoặc tự ưu ái khách VIP. (Điểm Faithfulness chạm đáy 1/5 và 2/5).
- **Thiếu hụt thông tin (Completeness):** Một số câu (q01, q06, q07) dù kéo đúng chunk nhưng LLM lại tóm tắt quá đà, làm mất đi các chi tiết quan trọng khiến điểm Completeness bị kéo xuống mức 2 và 3.