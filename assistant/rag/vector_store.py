import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from .embedder import embed_texts

try:
    import chromadb
except Exception:  # pragma: no cover - optional dependency at dev time
    chromadb = None  # type: ignore[assignment]


class VectorStore:
    """
    Lightweight wrapper around a persistent ChromaDB collection.

    Responsibilities:
    - Ensure the on-disk database folder exists.
    - Provide simple upsert and similarity search operations.
    - Maintain a rolling window of the last N conversation documents.
    """

    COLLECTION_NAME = "assistant_rag"

    def __init__(self, db_dir: Optional[Path] = None) -> None:
        self.log = logging.getLogger("rag.vector_store")

        if chromadb is None:
            raise RuntimeError(
                "chromadb is not installed. Install it to enable RAG."
            )

        if db_dir is None:
            db_dir = Path(__file__).resolve().parent / "chroma_db"

        self._db_dir = db_dir
        self._db_dir.mkdir(parents=True, exist_ok=True)

        try:
            self._client = chromadb.PersistentClient(path=str(self._db_dir))
            # Use cosine distance as requested.
            self._collection = self._client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as exc:  # pragma: no cover - runtime/hardware specific
            self.log.exception("Failed to initialise ChromaDB: %s", exc)
            raise

    # ------------------------------------------------------------------ #
    # Core operations
    # ------------------------------------------------------------------ #
    def upsert_documents(
        self,
        ids: List[str],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        if not ids or not documents:
            return

        if metadatas is None:
            metadatas = [{} for _ in ids]

        try:
            embeddings = embed_texts(documents)
            self._collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
            )
        except Exception as exc:  # pragma: no cover - runtime/hardware specific
            self.log.exception("Failed to upsert documents: %s", exc)

    def similarity_search(
        self,
        query: str,
        top_k: int = 3,
    ) -> List[str]:
        """
        Return the top_k most similar documents to the query.

        If the collection is empty or something goes wrong, an empty list
        is returned so the caller can gracefully fall back to normal LLM use.
        """
        try:
            if self._collection.count() == 0:
                return []

            query_vec = embed_texts([query])[0]
            result = self._collection.query(
                query_embeddings=[query_vec],
                n_results=top_k,
            )

            docs = result.get("documents") or []
            if not docs:
                return []
            # Chroma returns a list of lists for query results.
            return [str(d) for d in docs[0] if d]
        except Exception as exc:  # pragma: no cover - runtime/hardware specific
            self.log.exception("Similarity search failed: %s", exc)
            return []

    # ------------------------------------------------------------------ #
    # Conversation history helpers
    # ------------------------------------------------------------------ #
    def add_conversation(
        self,
        doc_id: str,
        document: str,
        metadata: Dict[str, Any],
        max_conversations: int = 100,
    ) -> None:
        """
        Store a single conversation turn (user question + assistant reply).

        Also enforces a rolling window of at most `max_conversations` entries.
        """
        try:
            self.upsert_documents([doc_id], [document], [metadata])
            self._prune_conversations(max_conversations)
        except Exception as exc:  # pragma: no cover
            self.log.exception("Failed to add conversation: %s", exc)

    def _prune_conversations(self, max_conversations: int) -> None:
        """
        Keep only the most recent `max_conversations` conversation docs.
        """
        try:
            # Chroma always returns IDs; we only need to explicitly ask
            # for metadatas here.
            results = self._collection.get(
                where={"type": "conversation"},
                include=["metadatas"],
            )
            ids = results.get("ids") or []
            metadatas = results.get("metadatas") or []

            if len(ids) <= max_conversations:
                return

            # Sort by timestamp metadata (oldest first).
            items = []
            for doc_id, meta in zip(ids, metadatas):
                ts = 0.0
                if isinstance(meta, dict):
                    ts = float(meta.get("timestamp", 0.0))
                items.append((ts, doc_id))

            items.sort(key=lambda x: x[0])
            to_delete = [doc_id for _, doc_id in items[:-max_conversations]]

            if to_delete:
                self._collection.delete(ids=to_delete)
        except Exception as exc:  # pragma: no cover
            self.log.exception("Failed to prune conversations: %s", exc)

