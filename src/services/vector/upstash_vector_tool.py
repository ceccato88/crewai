# src/generic_mm_project/upstash_vector_tool.py
import os
from typing import Any, Dict, List

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from upstash_vector import Index

from ..embeddings.voyage_embed import embed_query


class ArgsSchema(BaseModel):
    query: str = Field(..., description="Pergunta do usuário")
    top_k: int = Field(3, description="Número de resultados")


class UpstashVectorSearchTool(BaseTool):
    name: str = "UpstashVectorSearchTool"
    description: str = "Busca semântica no Upstash Vector"
    args_schema: Any = ArgsSchema

    def __init__(self, namespace: str | None = None):
        super().__init__()
        self._index = Index(
            url=os.getenv("UPSTASH_VECTOR_REST_URL"), token=os.getenv("UPSTASH_VECTOR_REST_TOKEN")
        )
        self._namespace = namespace or None

    def _run(self, query: str, top_k: int = 3) -> List[Dict]:
        vec = embed_query(query)
        res = self._index.query(
            vector=vec, top_k=top_k, include_metadata=True, namespace=self._namespace
        )
        # converte p/ formato similar ao Qdrant
        return [
            {"context": r.metadata.get("text", ""), "metadata": r.metadata, "distance": 1 - r.score}
            for r in res
        ]
