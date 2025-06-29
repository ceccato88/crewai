# src/services/vector/upstash_vector_tool.py
import json
import os
from typing import Any, List, Optional, Type, Callable

try:
    from upstash_vector import Index
    UPSTASH_AVAILABLE = True
except ImportError:
    UPSTASH_AVAILABLE = False
    Index = Any  # type placeholder

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from ..embeddings.voyage_embed import embed_query


class UpstashToolSchema(BaseModel):
    """Input schema for UpstashVectorSearchTool."""
    query: str = Field(
        ..., 
        description="Search query to find semantically similar documents"
    )
    top_k: int = Field(
        default=3, 
        description="Maximum number of results to return"
    )
    namespace: Optional[str] = Field(
        default=None,
        description="Optional namespace to search within"
    )
    include_vectors: bool = Field(
        default=False,
        description="Include vector values in response"
    )
    include_metadata: bool = Field(
        default=True,
        description="Include metadata in response"
    )
    include_data: bool = Field(
        default=True,
        description="Include data field in response"
    )
    filter: Optional[str] = Field(
        default=None,
        description="Metadata filter string (e.g., 'category = \"tech\"')"
    )


class UpstashVectorSearchTool(BaseTool):
    """Tool for semantic search using Upstash Vector database.
    
    This tool enables vector similarity search on documents stored in Upstash Vector,
    using Voyage AI embeddings for high-quality semantic matching.
    
    Attributes:
        name: Tool identifier
        description: Tool description for agents
        args_schema: Input validation schema
        upstash_url: Upstash Vector REST URL
        upstash_token: Upstash Vector REST token
        namespace: Default namespace for searches
        limit: Default number of results
        score_threshold: Minimum similarity score
        custom_embedding_fn: Custom embedding function (defaults to Voyage)
    """
    
    model_config = {"arbitrary_types_allowed": True}
    
    name: str = "UpstashVectorSearchTool"
    description: str = "Semantic search tool for Upstash Vector database using Voyage AI embeddings"
    args_schema: Type[BaseModel] = UpstashToolSchema
    
    # Configuration parameters
    upstash_url: Optional[str] = Field(
        default=None,
        description="Upstash Vector REST URL"
    )
    upstash_token: Optional[str] = Field(
        default=None, 
        description="Upstash Vector REST token"
    )
    namespace: Optional[str] = Field(
        default=None,
        description="Default namespace for searches"
    )
    limit: int = Field(
        default=3,
        description="Default number of results to return"
    )
    score_threshold: float = Field(
        default=0.35,
        description="Minimum similarity score threshold"
    )
    custom_embedding_fn: Optional[Callable[[str], List[float]]] = Field(
        default=None,
        description="Custom embedding function (defaults to Voyage AI)"
    )
    
    # Package dependencies for auto-installation
    package_dependencies: List[str] = ["upstash-vector"]
    
    # Private attributes
    _index: Optional[Any] = None

    def __init__(self, namespace: Optional[str] = None, **kwargs):
        """Initialize UpstashVectorSearchTool.
        
        Args:
            namespace: Optional default namespace for searches
            **kwargs: Additional configuration parameters
        """
        # Handle backward compatibility
        if namespace is not None:
            kwargs['namespace'] = namespace
            
        super().__init__(**kwargs)
        
        # Get credentials from parameters or environment
        url = self.upstash_url or os.getenv("UPSTASH_VECTOR_REST_URL")
        token = self.upstash_token or os.getenv("UPSTASH_VECTOR_REST_TOKEN")
        
        if not url:
            raise ValueError(
                "Upstash Vector URL is required. Set UPSTASH_VECTOR_REST_URL environment variable "
                "or pass upstash_url parameter."
            )
        
        if not token:
            raise ValueError(
                "Upstash Vector token is required. Set UPSTASH_VECTOR_REST_TOKEN environment variable "
                "or pass upstash_token parameter."
            )
        
        # Initialize Upstash client
        if UPSTASH_AVAILABLE:
            # Use from_env() if no explicit credentials provided
            if not self.upstash_url and not self.upstash_token:
                self._index = Index.from_env()
            else:
                self._index = Index(url=url, token=token)
        else:
            self._handle_missing_dependency()
    
    def _handle_missing_dependency(self):
        """Handle missing upstash-vector dependency."""
        try:
            import click
            if click.confirm(
                "The 'upstash-vector' package is required to use UpstashVectorSearchTool. "
                "Would you like to install it?"
            ):
                import subprocess
                subprocess.run(["uv", "add", "upstash-vector"], check=True)
                # Re-import after installation
                global Index, UPSTASH_AVAILABLE
                from upstash_vector import Index
                UPSTASH_AVAILABLE = True
                # Re-initialize with credentials
                url = self.upstash_url or os.getenv("UPSTASH_VECTOR_REST_URL")
                token = self.upstash_token or os.getenv("UPSTASH_VECTOR_REST_TOKEN")
                self._index = Index(url=url, token=token)
            else:
                raise ImportError(
                    "The 'upstash-vector' package is required. Install it with: uv add upstash-vector"
                )
        except ImportError:
            raise ImportError(
                "The 'upstash-vector' package is required. Install it with: uv add upstash-vector"
            )

    def _run(
        self, 
        query: str, 
        top_k: int = 3, 
        namespace: Optional[str] = None,
        include_vectors: bool = False,
        include_metadata: bool = True,
        include_data: bool = True,
        filter: Optional[str] = None
    ) -> str:
        """Execute vector similarity search on Upstash Vector.
        
        Args:
            query: Search query to vectorize and match
            top_k: Maximum number of results to return
            namespace: Optional namespace to search within
            include_vectors: Include vector values in response
            include_metadata: Include metadata in response
            include_data: Include data field in response
            filter: Metadata filter string (e.g., 'category = "tech"')
            
        Returns:
            JSON string containing search results with metadata and scores
            
        Raises:
            ImportError: If upstash-vector is not installed
            ValueError: If Upstash credentials are missing
            Exception: If search operation fails
        """
        if not self._index:
            raise ValueError("Upstash Vector client not initialized")
        
        try:
            # Use custom embedding function or default Voyage AI
            if self.custom_embedding_fn:
                vector = self.custom_embedding_fn(query)
            else:
                vector = embed_query(query)
            
            # Use provided namespace or default
            search_namespace = namespace or self.namespace
            
            # Prepare query parameters according to Upstash SDK
            query_params = {
                "vector": vector,
                "top_k": top_k,
                "include_vectors": include_vectors,
                "include_metadata": include_metadata,
                "include_data": include_data
            }
            
            # Add optional parameters
            if search_namespace:
                query_params["namespace"] = search_namespace
            if filter:
                query_params["filter"] = filter
            
            # Perform vector search using official Upstash SDK method
            search_results = self._index.query(**query_params)
            
            # Format results for compatibility
            results = []
            for result in search_results:
                # Apply score threshold filter
                if result.score >= self.score_threshold:
                    formatted_result = {
                        "id": result.id,
                        "score": result.score,
                        "distance": 1 - result.score,  # Convert score to distance for compatibility
                        "context": "",  # Will be filled from metadata or data
                        "metadata": result.metadata or {},
                    }
                    
                    # Add vector if requested
                    if include_vectors and hasattr(result, 'vector') and result.vector:
                        formatted_result["vector"] = result.vector
                    
                    # Add data if available
                    if include_data and hasattr(result, 'data') and result.data:
                        formatted_result["data"] = result.data
                        # Use data as context if available
                        formatted_result["context"] = result.data
                    
                    # Fallback to metadata text field for context
                    if not formatted_result["context"] and result.metadata:
                        formatted_result["context"] = result.metadata.get("text", "")
                    
                    results.append(formatted_result)
            
            return json.dumps(results, indent=2)
            
        except Exception as e:
            error_msg = f"Upstash Vector search failed: {str(e)}"
            return json.dumps({"error": error_msg}, indent=2)