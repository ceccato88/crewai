import os
from voyageai import Client as Voyage

voyage = Voyage(api_key=os.getenv("VOYAGE_API_KEY"))

def embed_doc(text: str):
    """Embedding para documentos (indexação)."""
    return voyage.embed(
        inputs=[{"content":[{"type":"text","text":text}]}],
        model="voyage-multimodal-3",
        input_type="document"
    ).embeddings[0]

def embed_query(text: str):
    """Embedding para consultas (busca)."""
    return voyage.embed(
        inputs=[{"content":[{"type":"text","text":text}]}],
        model="voyage-multimodal-3",
        input_type="query"
    ).embeddings[0]