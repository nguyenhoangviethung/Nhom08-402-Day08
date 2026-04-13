# Scorecard: Baseline Pipeline (Dense Retrieval)

**Người đánh giá:** [Nguyễn Thị Hương Giang]
**Thời gian đánh giá:** [...:..., 12/04/2026]
**Cấu hình Baseline:** `retrieval_mode="dense"`, `top_k=...`, `LLM=...`

## Tổng quan kết quả (Baseline)
- **Tổng điểm raw:** .../98
- **Điểm quy đổi (Hệ 30):** ... / 30
- **Số câu lấy đúng nguồn (Context Recall):** .../10 câu.
- **Số câu bị Hallucination (Penalty):** ... câu.

## Chi tiết đánh giá 10 câu Grading

| ID | Câu hỏi tóm tắt | Nguồn mong đợi | Nguồn Baseline lấy được | Faithfulness (Có bịa không?) | Điểm (Full/Partial/Zero/Penalty) | Nhận xét chi tiết (Bắt buộc nếu lỗi) |
|:---|:---|:---|:---|:---:|:---|:---|
| **gq01** | SLA P1 thay đổi thế nào so với bản trước? | `sla_p1_2026.txt` | `[Điền vào đây]` | [Pass/Fail] | [Điểm] | |
| **gq02** | Remote + VPN + giới hạn thiết bị? | Multi-docs | `[Điền vào đây]` | [Pass/Fail] | [Điểm] | |
| **gq03** | Flash Sale kích hoạt -> hoàn tiền không? | `policy_refund_v4.txt`| `[Điền vào đây]` | [Pass/Fail] | [Điểm] | |
| **gq04** | Store credit được bao nhiêu %? | `policy_refund_v4.txt`| `[Điền vào đây]` | [Pass/Fail] | [Điểm] | |
| **gq05** | Contractor cần Admin Access - điều kiện? | `access_control_sop.txt`| `[Điền vào đây]` | [Pass/Fail] | [Điểm] | |
| **gq06** | P1 lúc 2am -> cấp quyền tạm thời thế nào? | Multi-docs | `[Điền vào đây]` | [Pass/Fail] | [Điểm] | |
| **gq07** | Mức phạt vi phạm SLA P1 là bao nhiêu? | **KHÔNG CÓ** | `[Điền vào đây]` | **[Pass (Abstain) / Fail (Penalty)]** | [Điểm] | *Đặc biệt chú ý: Hệ thống phải trả lời 'Không có thông tin'* |
| **gq08** | Báo nghỉ phép 3 ngày = nghỉ ốm 3 ngày không?| `hr_leave_policy.txt` | `[Điền vào đây]` | [Pass/Fail] | [Điểm] | |
| **gq09** | Đổi pass mấy ngày, nhắc trước mấy ngày? | `it_helpdesk_faq.txt` | `[Điền vào đây]` | [Pass/Fail] | [Điểm] | |
| **gq10** | Chính sách v4 áp dụng đơn trước 01/02 không?| `policy_refund_v4.txt`| `[Điền vào đây]` | [Pass/Fail] | [Điểm] | |

## Nhận xét từ Eval Owner (Phân tích Baseline)

**1. Điểm sáng của cấu hình Baseline (Dense Search):**
[Ví dụ, hệ thống làm rất tốt ở các câu hỏi có keyword rõ ràng, trích xuất con số chính xác...]

**2. Điểm yếu / Failure Modes (Tại sao cần Variant?):**
[Ví dụ, thất bại ở các câu hỏi Multi-hop (gq02, gq06) do thuật toán Dense không kéo đủ thông tin từ nhiều nguồn khác nhau vào Top-3. Hoặc từ khóa bị nhiễu do khác tên gọi...]