# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Hoàng Đức Hưng  
**Vai trò trong nhóm:** Tech Lead / Eval Owner / Documentation Owner  
**Ngày nộp:** 13/4/2026  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

Trong lab này, tôi tham gia ở cả phần kỹ thuật lẫn phần đánh giá. Ở phía kỹ thuật, tôi đồng phát triển `index.py`, chủ yếu tập trung vào luồng indexing từ khâu preprocess, chunking, gắn metadata cho đến build index vào ChromaDB để toàn bộ pipeline có đầu vào ổn định. Công việc này kết nối trực tiếp với phần retrieval và generation của các bạn khác, vì nếu chunk hoặc metadata không đúng thì các bước sau dù prompt tốt cũng khó trả lời chính xác.

Ở phía đánh giá, tôi là người xây dựng và hoàn thiện `eval.py`, bao gồm luồng chạy scorecard cho baseline và variant, tổ chức các tiêu chí chấm điểm như Faithfulness, Relevance, Context Recall và Completeness, viết thêm phần `compare_ab()` để so sánh A/B giữa hai cấu hình, và `generate_grading_log()` để xuất log chấm theo đúng format yêu cầu. Tôi cũng trực tiếp chấm và tổng hợp kết quả ra `results/scorecard_baseline.md` và `results/scorecard_variant.md`. Về quá trình làm việc nhóm, tôi đã commit phần indexing lên branch `index`, commit phần đánh giá lên branch `eval`, sau đó tiếp tục commit tích hợp và hoàn thiện lên branch `main`. Ngoài ra, tôi tham gia tổng hợp nội dung cho `group_reports.md`, giúp nối phần kỹ thuật với phần nhận xét định tính của cả nhóm để báo cáo có mạch logic hơn.

_________________

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

Sau lab này, điều tôi hiểu rõ nhất là một hệ RAG không thể đánh giá chỉ bằng cảm giác “trả lời nghe có vẻ đúng”. Trước đây tôi thường nghĩ retrieve đúng tài liệu là gần như đủ, nhưng khi trực tiếp xây `eval.py` và nhìn scorecard từng câu, tôi thấy rõ retrieve đúng source chưa đồng nghĩa với câu trả lời cuối cùng đúng trọng tâm hoặc đầy đủ. Một pipeline RAG cần được nhìn thành nhiều lớp: indexing, retrieval, reranking/prompting và generation.

Tôi cũng hiểu rõ hơn ý nghĩa thực tế của 4 metric đánh giá. `Context Recall` trả lời câu hỏi “có kéo đúng bằng chứng về chưa”, còn `Faithfulness` kiểm tra “LLM có bám bằng chứng đó hay không”. `Completeness` lại là một lớp khác nữa: có trường hợp mô hình không bịa, không sai nguồn, nhưng vẫn trả lời thiếu ý quan trọng. Chính việc tách riêng các metric này giúp debug đúng chỗ thay vì sửa ngẫu nhiên.

_________________

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

Điều làm tôi ngạc nhiên nhất là baseline của nhóm đã đạt `Context Recall` rất cao, nhưng chất lượng trả lời tổng thể vẫn chưa thật sự mạnh. Ban đầu tôi có giả thuyết rằng chỉ cần thêm một variant retrieval như hybrid hoặc query expansion thì điểm sẽ tăng rõ rệt. Tuy nhiên, khi chấm và so sánh A/B trong `eval.py`, tôi thấy nhiều câu gần như không cải thiện, thậm chí có trường hợp còn xấu đi. Điều đó cho thấy bottleneck không phải lúc nào cũng nằm ở retrieval.

Khó khăn lớn nhất của tôi là làm sao thiết kế script đánh giá vừa đủ chặt chẽ để nhìn ra vấn đề, nhưng vẫn đủ đơn giản để cả nhóm có thể chạy lại nhiều lần. Nếu chấm quá cảm tính thì không dùng được, còn nếu làm quá phức tạp thì mất thời gian triển khai. Ngoài phần scorecard, tôi còn phải nghĩ cách chuẩn hóa đầu ra cho `grading log` và trình bày rõ chênh lệch ở phần `A/B comparison` để kết quả không chỉ “có số” mà còn thực sự hỗ trợ nhóm ra quyết định. Thực tế, phần tốn thời gian nhất không phải viết code mà là diễn giải kết quả sao cho cả nhóm hiểu được lỗi nằm ở đâu trong pipeline.

_________________

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

**Câu hỏi:** “Nếu cần hoàn tiền khẩn cấp cho khách hàng VIP, quy trình có khác không?”

**Phân tích:**

Đây là một câu tôi thấy rất hay vì nó kiểm tra đúng điểm yếu thật của hệ RAG: truy xuất đúng nhưng trả lời vẫn chưa tốt. Ở baseline, hệ thống retrieve được đúng tài liệu chính sách hoàn tiền nên `Context Recall` vẫn cao. Tuy nhiên, câu trả lời cuối lại chỉ dừng ở mức “không có thông tin” hoặc trả lời chưa đủ rõ rằng tài liệu không hề nêu quy trình riêng cho khách VIP, đồng thời chưa nhắc lại quy trình tiêu chuẩn 3-5 ngày làm việc đang áp dụng. Vì vậy điểm `Completeness` thấp và `Relevance` cũng không cao.

Theo tôi, lỗi chính của câu này không nằm ở indexing, vì tài liệu đã được index đúng và source được kéo về chuẩn. Lỗi cũng không hoàn toàn nằm ở retrieval, vì evidence phù hợp đã có trong context. Điểm nghẽn nằm ở generation: prompt chưa ép model phải vừa nêu phần “không có chính sách riêng”, vừa tận dụng phần thông tin chuẩn đang có để trả lời đầy đủ hơn.

Variant của nhóm không cải thiện đáng kể ở câu này. Đây là một kết quả quan trọng vì nó cho thấy thêm kỹ thuật retrieval chưa chắc xử lý được vấn đề nếu bản chất lỗi đang nằm ở cách model tổng hợp và diễn đạt câu trả lời từ context đã lấy về.

_________________

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

Nếu có thêm thời gian, tôi sẽ ưu tiên cải thiện prompt và cơ chế answer validation thay vì thêm nhiều retrieval variant mới. Kết quả eval cho thấy nhiều câu đã có đúng source nhưng mô hình vẫn trả lời thiếu hoặc lệch trọng tâm. Tôi muốn thử một bước hậu kiểm đơn giản: yêu cầu model tự đối chiếu lại câu trả lời với context trước khi trả ra cuối cùng, đặc biệt cho các câu dạng thiếu ngữ cảnh hoặc câu có yếu tố suy diễn như VIP, lỗi mã, ngoại lệ chính sách.

_________________

---
