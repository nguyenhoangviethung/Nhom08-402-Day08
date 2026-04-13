# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Mai Việt Hoàng
**Vai trò trong nhóm:** Tech Lead / Eval Owner
**Ngày nộp:** 13/04/2026
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

Trong lab này, tôi đảm nhận vai trò **Tech Lead / Eval Owner**, tập trung chủ yếu vào **Sprint 1** với nhiệm vụ hoàn thiện pipeline indexing trong file `index.py`.

Cụ thể, tôi đã implement **Step 3 (Embed + Store)** bằng cách tích hợp model embedding local `bkai-foundation-models/vietnamese-bi-encoder` thông qua thư viện Sentence Transformers, đọc cấu hình từ biến môi trường `LOCAL_EMBEDDING_MODEL` trong file `.env` để tiện thay đổi mà không cần sửa code. Tôi cũng hoàn thiện hàm `build_index()` để thực sự embed từng chunk và upsert vào ChromaDB với cosine similarity.

**Step 4 (Inspect)** tôi bật `list_chunks()` và `inspect_metadata_coverage()` để team có thể kiểm tra chất lượng index ngay sau khi build — bao gồm kiểm tra metadata đầy đủ và phân bố theo department.

Ngoài ra, tôi điều chỉnh `CHUNK_SIZE` từ 400 xuống 200 tokens và `CHUNK_OVERLAP` từ 80 xuống 40 tokens dựa trên giới hạn thực tế của model embedding (max 256 tokens/chunk). Công việc của tôi tạo ra ChromaDB index — nền tảng để các thành viên khác implement retrieval ở Sprint 2 và 3.

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

Sau lab này, tôi hiểu rõ hơn về **mối quan hệ giữa chunk size và embedding model** — điều mà trước đây tôi nghĩ chỉ là tham số tuỳ chọn.

Thực tế khi chạy, tôi phát hiện model `bkai-foundation-models/vietnamese-bi-encoder` có giới hạn cứng là **256 tokens** đầu vào. Nếu chunk vượt quá giới hạn này, model sẽ **tự cắt bỏ phần còn lại mà không báo lỗi** — nghĩa là embedding chỉ đại diện cho một phần chunk, không phải toàn bộ nội dung. Điều này dẫn đến retrieval kém chính xác dù pipeline không có lỗi nào hiển thị.

Bài học rút ra: trước khi chọn `CHUNK_SIZE`, phải kiểm tra `model.max_seq_length` của embedding model và trừ đi 2 special tokens `[CLS]`/`[SEP]`. Sau đó chọn chunk size ở khoảng 70–80% giới hạn để có buffer an toàn cho trường hợp tokenizer tiếng Việt sinh ra nhiều token hơn ước lượng ký tự/4.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

Khó khăn lớn nhất tôi gặp là **vấn đề môi trường và git workflow trong teamwork**. Ban đầu tôi implement embedding và build_index() rồi commit, nhưng sau đó cần `git pull` từ nhánh khác của team và chạy `git reset --hard origin/index` khiến toàn bộ thay đổi bị mất. Đây là bài học thực tế về việc cần **commit trước khi pull** hoặc **stash** thay đổi.

Ngoài ra, tôi ngạc nhiên khi thấy `chromadb` không có UI tích hợp để xem dữ liệu — trong khi các vector database thương mại như Pinecone hay Weaviate đều có dashboard. Phải dùng Jupyter Notebook kết hợp pandas để inspect chunk, và cũng gặp lỗi khi lưu embedding vector (shape 29×768) vào DataFrame vì pandas mặc định hiểu là 2D array thay vì list of objects.

Kết quả cuối cùng vẫn đạt được: 29 chunks được index đầy đủ, không chunk nào thiếu `effective_date`.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

**Câu hỏi:** *"Ai phải phê duyệt để cấp quyền Level 3?"*

**Phân tích:**

Câu hỏi này lấy từ file `access_control_sop.txt`, thông tin nằm ở **Section 2: Phân cấp quyền truy cập** — chunk `access_control_sop_1` trong index.

Với baseline (dense retrieval), câu hỏi này có khả năng được trả lời **đúng** vì:
1. Model embedding tiếng Việt `bkai-foundation-models/vietnamese-bi-encoder` được train trên dữ liệu tiếng Việt nên hiểu được query thuần Việt.
2. Chunk chứa thông tin rất cụ thể: *"Level 3 — Elevated Access: Áp dụng cho Team Lead, Senior Engineer, Manager. Phê duyệt: Line Manager + IT Admin + IT Security."*
3. Section nhỏ gọn, không bị cắt giữa điều khoản.

Điểm yếu tiềm năng: nếu query dùng từ đồng nghĩa như *"grant permission"* hay *"cấp phép hệ thống"* thay vì *"cấp quyền Level 3"*, dense retrieval có thể miss chunk này. Lúc đó hybrid retrieval (BM25 + dense) sẽ cải thiện nhờ keyword matching chính xác.

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

Tôi sẽ thử **hybrid chunking**: giữ section-based chunking cho các file policy/SOP, nhưng chuyển sang **Q&A-based chunking** riêng cho `it_helpdesk_faq.txt` — mỗi cặp Q+A là một chunk độc lập. Kết quả eval hiện tại cho thấy các câu hỏi dạng *"tôi cần làm gì khi..."* map tốt hơn với từng Q&A riêng lẻ thay vì phải retrieve cả section chứa 3-4 câu hỏi không liên quan.

---

