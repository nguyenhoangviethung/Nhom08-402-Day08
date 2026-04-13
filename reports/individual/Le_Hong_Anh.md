# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Lê Hồng Anh  
**Vai trò trong nhóm:** Tech Lead  
**Ngày nộp:** 13/04/2026  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

Trong lab này, tôi chịu trách nhiệm chính lập trình file `rag_answer.py`, tập trung chủ yếu vào việc xây dựng code cho Sprint 2 (Baseline Retrieval + Answer) và Sprint 3 (Tuning Tối Thiểu). Cụ thể, tôi đã trực tiếp implement các phương pháp truy vấn đa dạng vào hệ thống, bao gồm: tìm kiếm vector (Dense retrieval) qua ChromaDB, tìm kiếm từ khóa (Sparse retrieval) sử dụng thuật toán BM25, kết hợp Hybrid retrieval với thuật toán Reciprocal Rank Fusion (RRF), và thử nghiệm kỹ thuật Query Transformation. 

Về tính kết nối trong quy trình nhóm, công việc của tôi tiếp nối trực tiếp thành quả của thành viên làm Sprint 1 bằng cách gọi hàm `get_embedding` và đọc ChromaDB từ `index.py`. Đồng thời, các hàm lấy context và sinh câu trả lời do tôi viết ra chính là module cốt lõi để thành viên phụ trách (Eval Owner) trong Sprint 4 có thể gọi và chạy tự động các bài test trong file `eval.py`.

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

Khái niệm tôi thực sự hiểu sâu sắc và tâm đắc nhất sau lab này là **Hybrid Retrieval** và cách hoạt động của thuật toán **Reciprocal Rank Fusion (RRF)**. Trước đây, tôi thường lầm tưởng rằng chỉ cần nhúng câu văn thành vector (dense embedding) là đủ để AI có thể "hiểu" trọn vẹn ngữ nghĩa để tìm kiếm. Tuy nhiên, khi đối chiếu thực tế, dense retrieval thường hụt hơi khi cần tìm kiếm chính xác mã lỗi hay tên riêng. 

Hybrid retrieval là giải pháp hoàn hảo để kết hợp sức mạnh của cả hai thế giới: dense tìm theo ngữ nghĩa tổng quát, còn sparse (BM25) bám chặt vào các keyword cụ thể không được phép sai lệch. Điểm đặc biệt nhất là thuật toán RRF, giúp tôi hiểu cách hệ thống có thể kết hợp điểm số của hai bộ máy tìm kiếm hoàn toàn khác biệt nhau một cách công bằng (dựa trên rank thay vì score tuyệt đối) mà không cần phải huấn luyện thêm một model phức tạp nào khác.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

Điều khiến tôi ngạc nhiên nhất là việc Dense Retrieval (tìm kiếm vector) lại tỏ ra rất kém hiệu quả trước các truy vấn chứa từ khóa đồng nghĩa (alias) hoặc tên cũ của tài liệu, điều này dẫn đến việc trả về quá nhiều kết quả nhiễu (noise) thay vì tài liệu cần tìm. Giả thuyết ban đầu của tôi là các mô hình vector hiện đại đủ thông minh để tự động liên kết các từ đồng nghĩa trong không gian vector, nhưng thực tế bài lab đã chứng minh ngược lại.

Khó khăn mất nhiều thời gian debug nhất của tôi là khi implement phương pháp Hybrid bằng RRF. Việc hợp nhất và ánh xạ (map) lại các object document ban đầu từ hai danh sách kết quả (dense và sparse) rất dễ bị lỗi nếu trùng lặp text hoặc metadata bị sai lệch vị trí. Tôi đã phải debug cẩn thận vòng lặp hợp nhất này để đảm bảo đầu vào chuẩn xác nhất cho bước Generation.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

**Câu hỏi:** q07 - "Approval Matrix để cấp quyền hệ thống là tài liệu nào?"

**Phân tích:**
Đây là một query mang tính đánh đố (độ khó hard) vì người dùng cố tình truy vấn bằng tên cũ/alias ("Approval Matrix") thay vì tên file chuẩn hiện tại là "Access Control SOP". 

Dựa trên scorecard, cấu hình **baseline_dense** đã thất bại trong việc giải quyết triệt để câu hỏi này. Điểm Faithfulness tụt xuống rất thấp (2/5) và Completeness chỉ đạt (2/5). Lỗi gốc rễ nằm ở giai đoạn **Retrieval**: thuật toán dense truyền thống không tìm được khoảng cách ngữ nghĩa đủ gần giữa tên cũ và tên mới, dẫn đến việc lấy nhầm văn bản, từ đó LLM sinh ra câu trả lời (Generation) không có căn cứ hoặc đi chệch hướng.

Ngược lại, cấu hình **variant_hybrid** mang lại sự cải thiện nhảy vọt: điểm Faithfulness và Relevance đều đạt mức tối đa (5/5). Nhờ sự bổ trợ của thuật toán Sparse (BM25) quét chặt chẽ cụm từ khóa "Approval Matrix" kết hợp với văn cảnh chung từ Vector search, pipeline đã retrieve chính xác văn bản giải thích sự đổi tên tài liệu. Nhờ vậy, câu trả lời sinh ra bám sát hoàn toàn vào context được cung cấp.

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

Nếu có thêm thời gian, tôi sẽ thử nghiệm tinh chỉnh chuyên sâu các tham số trong mô hình Hybrid thay vì để cố định. Cụ thể, tôi sẽ điều chỉnh trọng số `dense_weight` và `sparse_weight` để đánh giá xem hệ thống ưu tiên keyword hay ngữ nghĩa sẽ cho ra Recall tốt hơn. Bên cạnh đó, tôi cũng muốn thay đổi hằng số phạt `k = 60` của thuật toán RRF thành các mức khác nhau để đo lường độ nhảy cảm của bảng xếp hạng, từ đó tìm ra điểm cân bằng tối ưu nhất cho tập dữ liệu IT Helpdesk.