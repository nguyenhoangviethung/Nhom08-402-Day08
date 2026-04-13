# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Nguyễn Thị Hương Giang  
**Vai trò trong nhóm:** Eval Owner / Documentation Owner  
**Ngày nộp:** 13/4/2026  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

- Đối chiếu mã nguồn để viết architecture.md và tổng hợp bảng điểm (scorecard_baseline.md, báo cáo nhóm).

_________________

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)
- Sau lab, tôi hiểu rõ bản chất của Evaluation Loop và sự khác biệt giữa hai chỉ số: Context Recall và Faithfulness.

_________________

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

Giả thuyết ban đầu là cấu hình Variant chắc chắn sẽ vượt trội hơn Baseline. Tuy nhiên, log thực tế cho thấy Variant không tăng được tổng điểm, thậm chí làm giảm nhẹ độ trung thực (Faithfulness tụt từ 4.30 xuống 4.20). Điều này dạy tôi rằng không phải kỹ thuật mở rộng nào cũng hiệu quả với mọi tập dữ liệu, và đánh giá là bước bắt buộc để xác nhận các giả thuyết.
_________________

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

**Câu hỏi:** "Lỗi ERR-403-AUTH xử lý như thế nào?"

**Phân tích:**
- Baseline: Trả lời sai (Hallucination). Điểm Context Recall là None (máy tìm kiếm đúng khi không gắp tài liệu nào lên), nhưng điểm Faithfulness chạm đáy 1/5.
- Lỗi ở đâu: Lỗi hoàn toàn ở khâu Generation. Mô hình gpt-4o phớt lờ lệnh "từ chối trả lời nếu thiếu thông tin", tự dùng kiến thức bên ngoài để bịa ra cách sửa lỗi.
- Variant có cải thiện không: Không. Cấu hình Variant vẫn nhận điểm 1/5. Việc LLM tự động mở rộng câu hỏi vô tình cung cấp thêm để hệ thống tự tin bịa chuyện logic hơn.
_________________

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

Kết quả eval cho thấy lỗi nghiêm trọng nhất nằm ở khâu Generation (lỗi bịa đặt khi thiếu thông tin). Nếu có thời gian, tôi sẽ thử thêm kỹ thuật Output Guardrail (Self-Correction). Tôi sẽ thiết lập một luồng LLM phụ chuyên làm giám khảo, ép nó tự đối chiếu lại câu trả lời với ngữ cảnh một lần cuối để gạt bỏ hoàn toàn các thông tin ảo giác.

_________________

---

