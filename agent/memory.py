"""
Persistent RAG memory for the model-selection loop -- same LanceDB +
LlamaIndex pattern as the sibling RSI gridworld project's agent/memory.py.
Embeddings via a local Ollama embedding model (nomic-embed-text), separate
from the qwen2.5:7b chat model used for proposals.
"""
from __future__ import annotations

from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.core.schema import TextNode
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.lancedb import LanceDBVectorStore
from llama_index.vector_stores.lancedb.base import TableNotFoundError

from agent.state import HistoryEntry

EMBED_MODEL = "nomic-embed-text"


class MDLMemory:
    def __init__(self, db_uri: str = "./lancedb", table_name: str = "mdl_memory"):
        Settings.embed_model = OllamaEmbedding(model_name=EMBED_MODEL)
        self._vector_store = LanceDBVectorStore(uri=db_uri, table_name=table_name)
        storage_context = StorageContext.from_defaults(vector_store=self._vector_store)
        self._index = VectorStoreIndex([], storage_context=storage_context)

    def store(self, entry: HistoryEntry) -> None:
        node = TextNode(text=self._entry_to_text(entry), metadata={"iteration": entry["iteration"]})
        self._index.insert_nodes([node])

    def retrieve(self, query: str, k: int = 3) -> list[str]:
        """Empty list if the memory has nothing yet -- including the very
        first call ever, before store() has created the underlying LanceDB
        table at all (found and handled the same way in the sibling
        project: retrieve() on a brand-new table raises rather than
        returning empty)."""
        retriever = self._index.as_retriever(similarity_top_k=k)
        try:
            results = retriever.retrieve(query)
        except TableNotFoundError:
            return []
        return [r.node.get_content() for r in results]

    @staticmethod
    def _entry_to_text(entry: HistoryEntry) -> str:
        m = entry["metrics"]
        return (
            f"family: {entry['config']['family']} | "
            f"metrics: accuracy_penalty={m['accuracy_penalty']}, complexity_score={m['complexity_score']}, "
            f"overall_score={m['overall_score']} | reflection: {entry['reflection']}"
        )
