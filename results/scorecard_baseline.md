# Scorecard: Baseline Pipeline (Dense Retrieval)

**Người đánh giá:** [Nguyễn Thị Hương Giang]
**Thời gian đánh giá:** [...:..., 12/04/2026]
**Cấu hình Baseline:** `retrieval_mode="dense"`, `top_k=...`, `LLM=...`

## Tổng quan kết quả (Baseline)
- **Tổng điểm raw:** .../98
- **Điểm quy đổi (Hệ 30):** ... / 30
- **Số câu lấy đúng nguồn (Context Recall):** .../10 câu.
- **Số câu bị Hallucination (Penalty):** ... câu.

## Chi tiết đánh giá 10 câu Test (Baseline)

| ID | Câu hỏi tóm tắt | Nguồn mong đợi | Nguồn Baseline lấy được | Faithfulness (Có bịa không?) | Điểm (Full/Partial/Zero/Penalty) | Nhận xét chi tiết (Bắt buộc nếu lỗi) |
|:---|:---|:---|:---|:---:|:---|:---|
| **q01** | SLA xử lý ticket P1 là bao lâu? | `sla_p1_2026.txt` | `[Điền vào đây]` | [Pass/Fail] | [Điểm] | |
| **q02** | Khách hàng có thể yêu cầu hoàn tiền trong bao nhiêu ngày? | `policy_refund_v4.txt`| `[Điền vào đây]` | [Pass/Fail] | [Điểm] | |
| **q03** | Ai phải phê duyệt để cấp quyền Level 3? | `access_control_sop.txt`| `[Điền vào đây]` | [Pass/Fail] | [Điểm] | |
| **q04** | Sản phẩm kỹ thuật số có được hoàn tiền không? | `policy_refund_v4.txt`| `[Điền vào đây]` | [Pass/Fail] | [Điểm] | *Đúng: AI phải từ chối hoàn tiền.* |
| **q05** | Tài khoản bị khóa sau bao nhiêu lần đăng nhập sai? | `it_helpdesk_faq.txt` | `[Điền vào đây]` | [Pass/Fail] | [Điểm] | |
| **q06** | Escalation trong sự cố P1 diễn ra như thế nào? | `sla_p1_2026.txt` | `[Điền vào đây]` | [Pass/Fail] | [Điểm] | |
| **q07** | Approval Matrix để cấp quyền hệ thống là tài liệu nào? | `access_control_sop.txt`| `[Điền vào đây]` | [Pass/Fail] | [Điểm] | *Đúng: Phải nhận diện được tên cũ.* |
| **q08** | Nhân viên được làm remote tối đa mấy ngày mỗi tuần? | `hr_leave_policy.txt` | `[Điền vào đây]` | [Pass/Fail] | [Điểm] | |
| **q09** | ERR-403-AUTH là lỗi gì và cách xử lý? | **KHÔNG CÓ (Rỗng)** | `[Điền vào đây]` | **[Pass (Abstain)]** | [Điểm] | *Đặc biệt: Hệ thống phải trả lời 'Không có thông tin', cấm bịa.* |
| **q10** | Hoàn tiền khẩn cấp cho khách hàng VIP, quy trình có khác không? | `policy_refund_v4.txt`| `[Điền vào đây]` | [Pass/Fail] | [Điểm] | *Đúng: AI phải nói quy trình không đổi (không nịnh khách VIP).* |


**1. Điểm sáng của cấu hình Baseline (Dense Search):**
[Ví dụ: Hệ thống làm rất tốt ở các câu hỏi trích xuất con số và quy định rõ ràng như q01, q02, q05...]

**2. Điểm yếu / Failure Modes (Tại sao cần Variant?):**

**2. Điểm yếu / Failure Modes (Tại sao cần Variant?):**
[Ví dụ: Baseline thất bại ở câu q07 vì đây là truy vấn bằng Tên cũ (Alias). Mô hình Vector không hiểu chữ "Approval Matrix" lại tương đồng với "Access Control SOP". Đồng thời cần kiểm tra kỹ q09 xem hệ thống có bịa lỗi không...]