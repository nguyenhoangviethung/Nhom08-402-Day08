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
- Sau lab, tôi hiểu rõ về tầm quan trọng của khâu xử lý dữ liệu là cực kì quan trọng hơn là các kĩ thuật
 retrival rag, nguyên lý cơ bản: garbage in, garbage out.
- Các kĩ trong RAG cũng quan trọng không kém: tuning các tham số sẽ giúp cho truy vấn hiệu quả hơn, ngoài ra việc lựa chọn 
kĩ thuật variant nào cũng tạo ra thay đổi perform đáng kể. Một truy vấn retrieval đúng chưa chắc đã cho kết quả đúng, nói chung là các kĩ thuật
liên quan phải được làm kĩ càng, kiểm tra cẩn thận.
- Hiểu được cách đánh giá Faithfulness, Answer Relevance, Context Recall, Completeness
_________________

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

- Variant luôn tốt hơn Baseline?? Tôi đã nghĩ vậy, tuy nhiên thực tế không hẳn vậy: Các log chỉ ra thường có kết quả hòa (Tie)
thật chí baseline còn có thể tốt hơn. (Xem log ở results)
- Tôi có cảm giác khó khăn khi tuning tham số, đôi lúc nó thực sự không thay đổi nhiều làm tôi không thể nhận ra lỗi sai ở đâu, hay các tiêu chí đánh giá kém tôi cũng phân vân không biết nên sửa lại kĩ thuật chunk hay system prompt hay kĩ thuật retrival. Mất thời gian khá lâu tôi mới năm bắt được. Đôi khi nhìn nhận sai về bản chất vấn đề, dễ đến ngõ cụt. Thật may team đã cùng nhau hỗ trợ để thực hiện bài lab này.
- Chương trình đã gợi ý dùng mô hình local embedding multi language, tuy nhiên tôi cảm thấy dùng model chuyên cho tiếng việt có lẽ sẽ tốt hơn. Và tôi khi thực hiện đã nhận ra mình thiếu 1 bước nữa: Mô hình embedding đó phân chia token có thể không hợp lý. Trong tiếng anh, 1 từ luôn có đủ nghĩ, tiếng việt thì không như vật, "hỗ trợ" là 1 từ nhưng có thể mô hình embedding thành 2 từ "hỗ" "trợ".
_________________

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

Phân tích scorecard: Câu q06 (Escalation sự cố P1)

- Phân tích chuyên sâu scorecard tại câu hỏi q06 cho thấy rõ giới hạn của cấu hình Baseline. Khi sử dụng Dense Search thuần túy, mặc dù chỉ số Context Recall đạt điểm tuyệt đối 5/5, điểm Completeness (Độ hoàn thiện) lại chỉ dừng ở mức 2/5. Cụ thể, LLM chỉ nhận diện được "Quy trình cấp quyền tạm thời 24h" (từ tài liệu Access Control) mà bỏ sót hoàn toàn điều kiện then chốt từ tài liệu SLA: "Tự động escalate lên Senior Engineer sau 10 phút".

- Nguyên nhân gốc rễ của sự cố này nằm ở khâu Retrieval với giới hạn top_k_select = 3. Thuật toán Vector Search đã thiên vị các đoạn văn bản dày đặc từ vựng về "sự cố P1", từ đó vô tình đẩy chunk chứa quy tắc 10 phút ra khỏi top ưu tiên, khiến LLM bị thiếu hụt ngữ cảnh trầm trọng.

- Tuy nhiên, cấu hình Variant tích hợp Hybrid Search đã khắc phục thành công nhược điểm này, nâng điểm Completeness lên mức 3/5. Nhờ bổ sung thuật toán BM25, hệ thống đã bắt chính xác các từ khóa đặc thù như "escalate" và "P1". Sự kết hợp này giúp truy xuất trọn vẹn dữ liệu từ cả hai tài liệu, tạo tiền đề lý tưởng để LLM thực hiện tổng hợp chéo (cross-document synthesis), kết hợp mượt mà cả quy trình 24h lẫn quy tắc 10 phút vào đáp án cuối cùng.
_________________

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

- Thách thức lớn nhất trong quá trình làm lab là việc tốn nhiều thời gian để nắm bắt mối liên hệ giữa các điểm số đánh giá thấp và kỹ thuật tuning tương ứng cần áp dụng. Điều này khiến tôi đành phải gác lại việc xây dựng các feature mới.
- Nếu có cơ hội tiếp tục tối ưu hóa, tôi sẽ ưu tiên nghiên cứu giải pháp xử lý dữ liệu đầu vào dạng ảnh scan từ PDF và áp dụng thử các phương thức Query Transformation phức tạp hơn để tối đa hóa hiệu năng truy xuất.
_________________

---
