# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Nguyễn Hoàng Việt Hùng
**Vai trò trong nhóm:** Tech lead / Eval Owner / Documentation Owner  
**Ngày nộp:** 13/4/2026  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

- Review mã nguồn index.py, rag_answer.py, eval.py
- Implement/Refactor index.py, eval.py
- Thực hiện bài tập grading_question.json
- Demo sản phẩm, trả lời câu hỏi về tech stack
- Review các file kết quả results/, các file logs/
_________________

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)
- Sau lab, tôi hiểu rõ về tầm quan trọng của xử lý dữ liệu đúng các trong retrival rag: garbage in, garbage out.
- Kĩ thuật trong RAG cũng quan trọng không kém: tuning các tham số sẽ giúp cho truy vấn hiệu quả hơn, ngoài ra việc lựa chọn 
kĩ thuật variant nào cũng tạo ra thay đổi perform đáng kể
- Hiểu được cách đánh giá Faithfulness, Answer Relevance, Context Recall, Completeness
_________________

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

- Variant luôn tốt hơn Baseline?? Tôi đã nghĩ vậy, tuy nhiên thực tế không hẳn vậy: Các log chỉ ra thường có kết quả hòa (Tie)
thật chí baseline còn có thể tốt hơn. (Xem log ở results)
- Tôi có cảm giác khó khăn khi tuning tham số, đôi lúc nó thực sự không thay đổi nhiều làm tôi không thể nhận ra lỗi sai ở đâu, hay các tiêu chí đánh giá 
kém tôi cũng phân vân không biết nên sửa lại kĩ thuật chunk hay system prompt hay kĩ thuật retrival. Mất thời gian khá lâu tôi mới năm bắt được
_________________

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

 scorecard: Câu q06 (Escalation sự cố P1)

- Baseline (Dense Search): Điểm Completeness chỉ đạt 2/5 (dù Recall 5/5). LLM chỉ nêu được quy trình "Cấp quyền tạm thời 24h" (từ Access Control) mà bỏ sót ý cốt lõi: "Tự động escalate lên Senior Engineer sau 10 phút" (từ SLA P1).

- Nguyên nhân: Lỗi ở khâu Retrieval do giới hạn top_k_select = 3. Vector Search ưu tiên đoạn văn mô tả cấp quyền (chứa nhiều từ vựng về "sự cố P1") và đẩy đoạn quy tắc 10 phút ra khỏi top 3, khiến LLM thiếu ngữ cảnh.

- Cải thiện ở Variant (Hybrid Search): Điểm Completeness tăng lên 3/5. Nhờ thuật toán BM25 bắt chính xác từ khóa "escalate" và "P1", hệ thống đã lấy đủ 2 tài liệu. LLM tổng hợp thành công cả quy trình 24h lẫn quy tắc 10 phút.
_________________

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

Mất khá nhiều thời gian để thực sự hiểu cần phải tune gì khi điểm nào thấp khiến tôi không thể tạo feature mới. Nếu có thêm thời gian tôi sẽ nghiên cứu 
tạo feature như: Input có thể là ảnh scan từ pdf, thử thêm các query_trasnform khác,..
_________________

---
