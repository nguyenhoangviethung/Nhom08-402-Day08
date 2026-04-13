import os
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DB_DIR = Path(__file__).parent / "chroma_db"

model_name = os.getenv(
    "LOCAL_EMBEDDING_MODEL",
    "bkai-foundation-models/vietnamese-bi-encoder"
)

model = SentenceTransformer(model_name)
client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
collection = client.get_collection("rag_lab")

queries = [
    "SLA xử lý ticket P1 là bao lâu?",
    "Ai phải phê duyệt để cấp quyền Level 3?",
    "Khách hàng có thể yêu cầu hoàn tiền trong bao nhiêu ngày?",
    "ERR-403-AUTH",
]

for query in queries:
    print("\n" + "=" * 70)
    print("QUERY:", query)

    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3,
        include=["documents", "metadatas", "distances"]
    )

    for i, (doc, meta, dist) in enumerate(
        zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ),
        start=1
    ):
        print(f"\nTop {i}")
        print("Distance:", round(dist, 4))
        print("Source:", meta.get("source"))
        print("Section:", meta.get("section"))
        print("Text:", doc[:300], "...")
