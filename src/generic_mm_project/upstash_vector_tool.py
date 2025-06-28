from typing import Any, Dict, List
from pydantic import BaseModel, Field
from upstash_vector import Index
from crewai_tools import tool
from .voyage_embed import embed_query
import os

class ArgsSchema(BaseModel):
    query: str = Field(..., description="Pergunta do usuário")
    top_k: int = Field(3, description="Número de resultados")

def upstash_vector_search_tool(query: str, top_k: int = 3, namespace: str = "") -> List[Dict]:
    """Busca semântica no Upstash Vector"""
    url = os.getenv("UPSTASH_VECTOR_REST_URL")
    token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
    
    if url is None:
        raise ValueError("UPSTASH_VECTOR_REST_URL environment variable not set")
    if token is None:
        raise ValueError("UPSTASH_VECTOR_REST_TOKEN environment variable not set")
        
    index = Index(url=url, token=token)
    namespace = namespace or None
        vec = embed_query(query)
    res = index.query(
        vector=vec,
        top_k=top_k,
        include_metadata=True,
        namespace=namespace
    )
    # converte p/ formato similar ao Qdrant
    return [{
        "context": r.metadata.get("text", ""),
        "metadata": r.metadata,
        "distance": 1 - r.score
    } for r in res]

UpstashVectorSearchTool = tool(upstash_vector_search_tool)
