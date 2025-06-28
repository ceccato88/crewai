from typing import Any, Dict, List
from pydantic import BaseModel, Field
from upstash_vector import Index
from crewai_tools import BaseTool
from .voyage_embed import embed_query
import os

class ArgsSchema(BaseModel):
    query: str = Field(..., description="Pergunta do usuário")
    top_k: int = Field(3, description="Número de resultados")

class UpstashVectorSearchTool(BaseTool):
    name: str = "UpstashVectorSearchTool"
    description: str = "Busca semântica no Upstash Vector"
    args_schema: Any = ArgsSchema

    def __init__(self, namespace: str = ""):
        super().__init__()
        url = os.getenv("UPSTASH_VECTOR_REST_URL")
        token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
        
        if url is None:
            raise ValueError("UPSTASH_VECTOR_REST_URL environment variable not set")
        if token is None:
            raise ValueError("UPSTASH_VECTOR_REST_TOKEN environment variable not set")
            
        self.index = Index(url=url, token=token)
        self.namespace = namespace or None

    def _run(self, query: str, top_k: int = 3) -> List[Dict]:
        vec = embed_query(query)
        res = self.index.query(
            vector=vec,
            top_k=top_k,
            include_metadata=True,
            namespace=self.namespace
        )
        # converte p/ formato similar ao Qdrant
        return [{
            "context": r.metadata.get("text", ""),
            "metadata": r.metadata,
            "distance": 1 - r.score
        } for r in res]
