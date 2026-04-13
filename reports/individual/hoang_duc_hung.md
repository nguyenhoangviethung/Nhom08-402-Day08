# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Hoàng Đức Hưng  
**Vai trò trong nhóm:** Tech Lead / Eval Owner / Documentation Owner  
**Ngày nộp:** 13/4/2026  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

Trong nhóm, tôi tham gia chủ yếu ở hai mảng là **indexing** và **evaluation**, và các phần tôi khai báo dưới đây tương ứng với những commit tôi thực hiện trên nhánh `main` bằng tài khoản GitHub `selffullfilling-prophecy` (trong log local phần author name có thể hiển thị là `Ngay mua gio`). Cụ thể, ở commit `32a41e3` tôi xử lý phần `preprocess + chunk` trong `index.py`, gồm việc parse metadata từ header tài liệu, làm sạch văn bản và tách tài liệu theo section/paragraph để phục vụ retrieval. Sau đó, ở commit `e203593` tôi phát triển mạnh phần `eval.py`: hoàn thiện pipeline chấm điểm baseline/variant, viết `compare_ab()`, `generate_grading_log()`, đồng thời sinh các file `results/scorecard_baseline.md`, `results/scorecard_variant.md`, `results/ab_comparison.csv`. Ở commit `11c4054`, tôi tiếp tục cập nhật cấu hình variant theo hướng rerank, thêm `data/grading_questions.json` và xuất `logs/grading_run.json`. Ngoài ra, tôi còn cập nhật phần báo cáo nhóm ở commit `5c8b4bf`.

_________________

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

Sau lab này, tôi hiểu rõ hơn rằng chất lượng của một hệ RAG không nằm ở một bước riêng lẻ, mà là kết quả của cả chuỗi từ **chunking, retrieval, prompting đến evaluation**. Khi trực tiếp làm `index.py`, tôi thấy chunk không thể chỉ cắt theo độ dài một cách cơ học. Nếu chunk bị trộn nhiều ý hoặc cắt giữa điều khoản, mô hình có thể retrieve đúng source nhưng vẫn trả lời sai trọng tâm. Vì vậy metadata như `source`, `section`, `effective_date`, `department` rất quan trọng để truy xuất và giải thích kết quả.

Ở phần `eval.py`, tôi hiểu rõ hơn ý nghĩa của từng metric. `Context Recall` chỉ cho biết retriever có mang về đúng evidence hay không. Nhưng một hệ có `Context Recall` cao vẫn có thể trả lời chưa tốt nếu prompt chưa đủ grounding hoặc chunk top-k chưa phải là chunk đúng trọng tâm nhất. Chính vì vậy, khi đọc scorecard tôi luôn phải nhìn đồng thời cả `Faithfulness`, `Relevance` và `Completeness`, thay vì chỉ nhìn một chỉ số duy nhất.

_________________

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

Điều làm tôi ngạc nhiên nhất là **retrieval đúng chưa chắc answer tốt**. Khi triển khai `compare_ab()` và nhìn bảng so sánh baseline với variant, tôi nhận ra có nhiều câu hỏi mà `Context Recall` gần như tối đa, nhưng `Completeness` vẫn thấp hoặc `Faithfulness` vẫn chưa ổn. Điều đó cho thấy nút thắt không chỉ nằm ở retriever mà còn ở cách chọn chunk cuối cùng và cách LLM tổng hợp câu trả lời.

Khó khăn lớn nhất của tôi là xây dựng phần evaluation sao cho vừa đủ chặt chẽ để nhóm dùng làm căn cứ ra quyết định. Nếu chỉ ghi nhận “variant tốt hơn” mà không có số liệu per-question thì rất khó thuyết phục. Vì vậy tôi phải làm thêm hai phần mà tôi thấy rất hữu ích: `compare_ab()` để nhìn delta theo từng metric và từng câu, và `generate_grading_log()` để chuẩn hóa đầu ra khi chạy bộ grading questions. Phần này giúp quá trình chấm không bị cảm tính và dễ truy vết hơn khi debug.

_________________

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

**Câu hỏi:** “Nếu cần hoàn tiền khẩn cấp cho khách hàng VIP, quy trình có khác không?”

**Phân tích:**

Đây là câu hỏi tôi thấy tiêu biểu cho việc **retrieval không phải lúc nào cũng là bottleneck chính**. Khi chạy scorecard, hệ thống vẫn retrieve được đúng tài liệu `policy/refund-v4.pdf`, nên về mặt `Context Recall` có thể xem là ổn. Tuy nhiên, câu trả lời cuối cùng vẫn chưa thật sự tốt vì mô hình chỉ dừng ở mức nói “không có thông tin” hoặc trả lời chưa đầy đủ rằng tài liệu không hề nêu một quy trình riêng cho khách VIP, trong khi vẫn có thể nhắc lại quy trình hoàn tiền tiêu chuẩn là 3–5 ngày làm việc.

Theo cách nhìn của tôi, lỗi ở đây không nằm ở `indexing`, vì policy refund đã được index và retrieve đúng. Lỗi cũng không hoàn toàn nằm ở `retrieval`, vì bằng chứng liên quan đã có trong context. Vấn đề chính nằm ở `generation`: prompt chưa ép mô hình trả lời theo hướng “không có chính sách riêng cho VIP, nên áp dụng quy trình chuẩn hiện có trong tài liệu”. Đây cũng là lý do câu này rất hữu ích trong scorecard: nó giúp tôi phân biệt được sự khác nhau giữa “kéo đúng tài liệu” và “trả lời đúng, đủ, bám bằng chứng”.

_________________

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

Nếu có thêm thời gian, tôi sẽ tiếp tục cải thiện nhánh evaluation theo hai hướng. Thứ nhất là bổ sung guardrail cho các câu hỏi dạng thiếu ngữ cảnh hoặc dễ gây suy diễn, để mô hình abstain tốt hơn thay vì chỉ nói “Tôi không biết”. Thứ hai là mở rộng `compare_ab()` theo nhóm lỗi, ví dụ tách riêng câu hỏi về temporal reasoning, exception policy, cross-document synthesis, vì score tổng đôi khi che mất việc một cấu hình chỉ tốt ở một nhóm câu hỏi rất cụ thể.

_________________

---
