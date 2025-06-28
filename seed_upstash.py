import os
import uuid
from upstash_vector import Index
from src.generic_mm_project.voyage_embed import embed_doc

index = Index.from_env()   # lê URL/TOKEN do .env

EXAMPLES = [
    ("doc1.txt", "imgs/doc1.jpg",
     "Documento 1: explica grafos temporais."),
    ("doc2.txt", "imgs/doc2.jpg",
     "Documento 2: descreve indexação vetorial."),
]

for file, img, text in EXAMPLES:
    index.upsert(vectors=[
        (
            str(uuid.uuid4()),
            embed_doc(text),
            {"file": file, "text": text, "image_path": os.path.abspath(img)}
        )
    ])
print("🏁 Upstash populado com", len(EXAMPLES), "vetores.")
