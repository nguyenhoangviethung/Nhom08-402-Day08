# Architecture — RAG Pipeline (Day 08 Lab)

> Template: Điền vào các mục này khi hoàn thành từng sprint.
> Deliverable của Documentation Owner.

## 1. Tổng quan kiến trúc

```
[Raw Docs]
    ↓
[index.py: Preprocess → Chunk → Embed → Store]
    ↓
[ChromaDB Vector Store]
    ↓
[rag_answer.py: Query → Retrieve → Rerank → Generate]
    ↓
[Grounded Answer + Citation]
```

**Mô tả ngắn gọn:**
> TODO: Mô tả hệ thống trong 2-3 câu. Nhóm xây gì? Cho ai dùng? Giải quyết vấn đề gì?
Xây dựng hệ thống Trợ lý ảo nội bộ (RAG Pipeline) phục vụ cho khối Customer Success (CS) và IT Helpdesk. Hệ thống tự động tra cứu, trích xuất và tổng hợp thông tin từ các tài liệu nghiệp vụ (Chính sách nhân sự, SLA, Quy trình cấp quyền) để trả lời các câu hỏi nghiệp vụ một cách chính xác, có kiểm chứng (Grounded) và ngăn chặn tuyệt đối tình trạng sinh ảo giác (Hallucination).
---

## 2. Indexing Pipeline (Sprint 1)

### Tài liệu được index
| File | Nguồn | Department | Số chunk |
|------|-------|-----------|---------|
| `policy_refund_v4.txt` | policy/refund-v4.pdf | CS | 6|
| `sla_p1_2026.txt` | support/sla-p1-2026.pdf | IT | 5 |
| `access_control_sop.txt` | it/access-control-sop.md | IT Security | 7 |
| `it_helpdesk_faq.txt` | support/helpdesk-faq.md | IT | 6 |
| `hr_leave_policy.txt` | hr/leave-policy-2026.pdf | HR | 5 |

### Quyết định chunking
| Tham số | Giá trị | Lý do |
|---------|---------|-------|
| Chunk size | 200 | Phù hợp với giới hạn max_seq_length (256) của model Bi-Encoder để tránh mất thông tin khi embedding. |
| Overlap | 50 | Đảm bảo tính liên kết ngữ cảnh giữa các đoạn văn bản khi bị cắt nhỏ. |
| Chunking strategy | Heading-based | Các tài liệu nghiệp vụ (SOP, Policy, SLA) có cấu trúc phân cấp chặt chẽ. Cắt theo Heading giúp giữ trọn vẹn một quy trình hoặc một điều khoản chính sách trong cùng một chunk, tránh tình trạng một bước hướng dẫn bị tách rời khỏi ngữ cảnh của nó. |
| Metadata fields | chunk_id, source, department,	section,	effective_date,	access,	text | Phục vụ filter, freshness, citation |

### Embedding model
- **Model**: bkai-foundation-models/vietnamese-bi-encoder
- **Vector store**: ChromaDB (PersistentClient)
- **Similarity metric**: Cosine (`hnsw:space: cosine`)

---

## 3. Retrieval Pipeline (Sprint 2 + 3) (chưa làm)

### Baseline (Sprint 2)
| Tham số | Giá trị |
|---------|---------|
| Strategy | Dense + Rerank |
| Top-k search | 10 |
| Top-k select | 3 |
| Rerank | Không |

### Variant (Sprint 3)
| Tham số | Giá trị | Thay đổi so với baseline |
|---------|---------|------------------------|
| Strategy | hybrid | thêm rerank |
| Top-k search | 10 | Giữ nguyên số lượng ứng viên truy xuất ban đầu từ ChromaDB. |
| Top-k select | 3 | Giữ nguyên số lượng chunk tối ưu đưa vào Prompt để tránh nhiễu ngữ cảnh. |
| Rerank | BAAI/bge-reranker-v2-m3 | Sử dụng mô hình Cross-encoder để xếp hạng lại độ liên quan của các chunk. |
| Query transform | expansion | Sử dụng LLM để mở rộng câu hỏi gốc (sinh thêm từ đồng nghĩa, ngữ cảnh) trước khi đưa đi tìm kiếm vector. Giúp bắt dính các tài liệu dùng từ vựng khác với truy vấn của user (như tên tài liệu cũ, alias). | |

**Lý do chọn variant này:**
> TODO: Giải thích tại sao chọn biến này để tune.
> Nhóm quyết định chọn Reranker vì kết quả Baseline cho thấy hệ thống đôi khi lấy đúng tài liệu nhưng chưa ưu tiên được chunk chứa câu trả lời chính xác nhất lên đầu. Việc dùng Reranker giúp lọc nhiễu và đảm bảo 3 chunk đưa vào LLM là 3 mảnh ghép có giá trị thông tin cao nhất, từ đó cải thiện độ hoàn thiện của câu trả lời.

---

## 4. Generation (Sprint 2)

### Grounded Prompt Template
```
Bạn là một trợ lý AI hữu ích. Hãy trả lời câu hỏi CHỈ dựa trên ngữ cảnh dưới đây.
    Nếu ngữ cảnh không đủ, hãy nói bạn không biết. Hãy trích dẫn nguồn bằng số thứ tự trong ngoặc vuông [1].
    Hãy trả lời bằng Tiếng Việt.

    Question: {query}

    Context:
    {context_block}

    Answer:"""
```

### LLM Configuration
| Tham số | Giá trị |
|---------|---------|
| Model | openAI-4o|
| Temperature | 0 (để output ổn định cho eval) |
| Max tokens | 256 |

---

## 5. Failure Mode Checklist

> Dùng khi debug — kiểm tra lần lượt: index → retrieval → generation

| Failure Mode | Triệu chứng | Cách kiểm tra (Dựa trên code thực tế) |
|-------------|-------------|---------------|
| Index lỗi | Thiếu metadata (đặc biệt là ngày hiệu lực) dẫn đến không kiểm soát được version tài liệu. | Chạy hàm `inspect_metadata_coverage()` trong `index.py` để xem thống kê "Chunks thiếu effective_date". |
| Chunking tệ | Chunk bị hụt ý hoặc lưu sai section. | Chạy hàm `list_chunks()` trong `index.py` để đối chiếu `Section` và đọc `Text preview`. |
| Retrieval lỗi | Không lấy được tài liệu đích (expected sources) để trả lời. | Xem điểm số và ghi chú sinh ra từ hàm `score_context_recall()` trong `eval.py`. Hàm này sẽ liệt kê chi tiết danh sách tài liệu bị `missing`. |
| Generation lỗi | Sinh câu trả lời bịa đặt (hallucinate) hoặc không dựa vào tài liệu (not grounded). | Kiểm tra kết quả từ hàm `score_faithfulness()` trong `eval.py` (nếu điểm = 1 tức là LLM đang bịa thông tin hoàn toàn). |
| Token overload | Mất thông tin do context đẩy vào LLM quá dài. | Trong `eval.py`, hàm `_build_chunks_text()` đã thiết lập sẵn cơ chế phòng vệ bằng tham số `max_chars=5000` để tự động cắt bớt context nếu quá dài. |

---

## 6. Diagram (tùy chọn)

> TODO: Vẽ sơ đồ pipeline nếu có thời gian. Có thể dùng Mermaid hoặc drawio.

```mermaid
graph LR
A[User Query] --> B{Sử dụng Query Transform?}
    B -->|Có (Variant)| C[Query Expansion]
    B -->|Không (Baseline)| D[Query Embedding]
    C --> D
    
    D --> E[(ChromaDB Vector Search)]
    E --> F[Top-10 Candidates]
    
    F --> G{Sử dụng Rerank?}
    G -->|Có (Variant)| H[Cross-Encoder: BAAI/bge-reranker-v2-m3]
    G -->|Không (Baseline)| I[Top-3 Select]
    
    H --> I
    I --> J[Build Context Block]
    J --> K[Grounded Prompt]
    K --> L((LLM: gpt-4o-mini))
    L --> M[Answer + Citation]
```
