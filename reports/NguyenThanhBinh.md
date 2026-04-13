# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Nguyễn Thanh Bình  
**Vai trò trong nhóm:** Eval Owner / Documentation Owner  
**Ngày nộp:** 13/04/2026  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

Trong dự án RAG Pipeline này, tôi đảm nhận hai vai trò ở giai đoạn cuối là Eval Owner và Documentation Owner. Trọng tâm công việc của tôi nằm ở Sprint 3 và Sprint 4, nơi tôi chịu trách nhiệm thiết kế khung đánh giá A/B Testing để so sánh hiệu quả giữa Baseline (Dense Retrieval) và Variant (Query Expansion). Tôi trực tiếp chạy pipeline eval với `eval.py` trên 10 câu hỏi trong `test_questions.json`, sử dụng LLM-as-Judge (gpt-4o-mini) để chấm 4 metrics: Faithfulness, Answer Relevance, Context Recall và Completeness. Kết quả được tổng hợp vào `scorecard_variant.md`. Song song đó, tôi quản lý `tuning-log.md`, ghi lại chi tiết config, giả thuyết nguyên nhân lỗi, kết quả thực tế và kết luận sau mỗi lần thử nghiệm — bao gồm cả việc phát hiện và sửa bug duplicate key trong `rag_answer.py` làm vô hiệu hóa tham số `use_transform`.

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

Sau lab này, tôi hiểu rõ hơn về tầm quan trọng của việc **đo lường trước khi tối ưu**. Trước đây tôi nghĩ cứ thêm kỹ thuật mới (Query Expansion, Hybrid Search) là hệ thống sẽ tốt hơn. Nhưng thực tế cho thấy Baseline với dense retrieval và embedding model tiếng Việt (`bkai-foundation-models/vietnamese-bi-encoder`) đã đạt Context Recall 5.00/5 ngay từ đầu — tức là retrieval không phải bottleneck. Khi chạy Variant với Query Expansion, delta bằng 0 trên tất cả metrics, chứng minh rằng giả thuyết ban đầu sai. Điều này dạy tôi một nguyên tắc quan trọng: phải đọc kỹ scorecard để xác định đúng điểm yếu trước khi chọn biến để tune. Trong trường hợp này, bottleneck thực sự nằm ở Generation — LLM trả lời lệch trọng tâm dù đã retrieve đúng chunk.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

Tôi ngạc nhiên khi **Baseline hoạt động tốt hơn kỳ vọng** — đạt Faithfulness 4.30/5 và Context Recall 5.00/5 ngay từ lần chạy đầu tiên. Điều này trái ngược với giả định ban đầu rằng dense search sẽ bỏ lỡ các thuật ngữ chuyên ngành. Thực tế là embedding model tiếng Việt đã xử lý tốt ngữ nghĩa của corpus. Khó khăn lớn nhất là khi kết quả Variant không cải thiện so với Baseline — tôi phải đối mặt với việc ghi nhận trung thực thay vì "làm đẹp" số liệu. Một khó khăn kỹ thuật khác là phát hiện bug trong `rag_answer.py`: có hai dòng `"use_transform"` trong cùng một dict, dòng sau ghi đè dòng trước thành `False`, khiến Query Expansion chưa bao giờ thực sự chạy trong các lần test trước. Phải sửa bug này trước khi có kết quả eval đáng tin cậy.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

**Câu hỏi:** "Approval Matrix để cấp quyền hệ thống là tài liệu nào?" (ID: q07)

**Phân tích:**
Đây là câu hỏi tiêu biểu minh chứng cho sự phức tạp của bài toán Generation trong RAG.

- **Baseline:** Faithfulness 5, Relevance 5, Context Recall 5, Completeness **2**. Hệ thống retrieve đúng file `access-control-sop.md` (recall = 5/5), nhưng LLM trả lời bằng cách mô tả chức năng của tài liệu thay vì nêu tên tài liệu — đây chính xác là điều câu hỏi yêu cầu. Expected answer là: *"Tài liệu 'Approval Matrix for System Access' hiện tại có tên mới là 'Access Control SOP'"*.
- **Variant 1 (Query Expansion):** Kết quả giống hệt Baseline — 5/5/5/2. Query Expansion không giúp ích vì vấn đề không phải ở retrieval mà ở generation: LLM nhận đúng chunk nhưng không trả lời đúng trọng tâm câu hỏi.
- **Kết luận:** q07 cho thấy rằng Context Recall cao không đảm bảo Completeness cao. Để cải thiện câu này, cần điều chỉnh prompt để hướng dẫn LLM trả lời đúng dạng câu hỏi (tên tài liệu) thay vì mô tả nội dung. Đây là insight quan trọng nhất tôi ghi lại trong `tuning-log.md`.

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

Nếu có thêm thời gian, tôi sẽ thử hai hướng song song. Thứ nhất, triển khai **Reranking** (Cross-Encoder `BAAI/bge-reranker-v2-m3`) để đưa chunk đúng trọng tâm lên đầu context, nhằm cải thiện Completeness hiện đang ở 3.40/5 — đặc biệt cho q06 và q07. Thứ hai, cải thiện **prompt template** để hướng dẫn LLM trả lời đúng dạng câu hỏi thay vì mô tả toàn bộ nội dung chunk. Hai thay đổi này nhắm trực tiếp vào bottleneck đã xác định được: Generation, không phải Retrieval.
