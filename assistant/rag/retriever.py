import logging
import time
from pathlib import Path
from typing import List

from .vector_store import VectorStore


class RagRetriever:
    """
    High-level RAG orchestration for the assistant.

    - Loads and chunks the knowledge base at startup.
    - Provides context retrieval for user questions.
    - Stores conversation history into the same vector store.
    """

    def __init__(self) -> None:
        self.log = logging.getLogger("rag.retriever")

        # Resolve directory structure relative to the assistant package.
        rag_dir = Path(__file__).resolve().parent
        assistant_root = rag_dir.parent
        kb_dir = assistant_root / "data" / "knowledge_base"

        self.store = VectorStore(db_dir=rag_dir / "chroma_db")

        # Ensure the KB directory exists and index its contents.
        kb_dir.mkdir(parents=True, exist_ok=True)
        self._index_knowledge_base(kb_dir)

    # ------------------------------------------------------------------ #
    # Knowledge base indexing
    # ------------------------------------------------------------------ #
    def _index_knowledge_base(self, kb_dir: Path) -> None:
        """
        Load all .txt files from the knowledge base directory, chunk them,
        and upsert into the persistent vector store.
        """
        try:
            ids: List[str] = []
            docs: List[str] = []
            metas: List[dict] = []

            for txt_path in sorted(kb_dir.glob("*.txt")):
                try:
                    content = txt_path.read_text(encoding="utf-8").strip()
                except Exception as exc:
                    self.log.exception("Failed to read %s: %s", txt_path, exc)
                    continue

                if not content:
                    continue

                chunks = self._chunk_text(content, chunk_size=500, overlap=100)
                for idx, chunk in enumerate(chunks):
                    doc_id = f"kb::{txt_path.name}::chunk::{idx}"
                    ids.append(doc_id)
                    docs.append(chunk)
                    metas.append(
                        {
                            "type": "kb",
                            "source": txt_path.name,
                            "chunk_index": idx,
                        }
                    )

            if ids:
                self.store.upsert_documents(ids, docs, metas)
                self.log.info(
                    "Indexed %d KB chunks from %s", len(ids), kb_dir
                )
            else:
                self.log.info("No KB .txt files found in %s", kb_dir)
        except Exception as exc:  # pragma: no cover - runtime specific
            self.log.exception("Failed to index knowledge base: %s", exc)

    @staticmethod
    def _chunk_text(
        text: str,
        chunk_size: int,
        overlap: int,
    ) -> List[str]:
        """
        Simple character-based chunking with fixed overlap.

        This keeps memory use very small while still providing enough
        context for RAG on a constrained device.
        """
        if chunk_size <= 0:
            return [text]

        chunks: List[str] = []
        start = 0
        length = len(text)
        step = max(1, chunk_size - overlap)

        while start < length:
            end = min(length, start + chunk_size)
            chunks.append(text[start:end])
            start += step

        return chunks

    # ------------------------------------------------------------------ #
    # Retrieval
    # ------------------------------------------------------------------ #
    def retrieve_context(self, query: str, top_k: int = 3) -> List[str]:
        """
        Retrieve the most relevant text chunks for the given query.

        Any failure returns an empty list so the caller can fall back to
        normal LLM behaviour without breaking the assistant.
        """
        if not query.strip():
            return []

        try:
            return self.store.similarity_search(query, top_k=top_k)
        except Exception as exc:  # pragma: no cover
            self.log.exception("RAG retrieval failed: %s", exc)
            return []

    # ------------------------------------------------------------------ #
    # Conversation memory
    # ------------------------------------------------------------------ #
    def add_conversation(self, question: str, answer: str) -> None:
        """
        Store a single Q&A turn into the vector store so that future
        retrieval can leverage conversational history as additional context.
        """
        q = (question or "").strip()
        a = (answer or "").strip()
        if not q and not a:
            return

        try:
            ts = time.time()
            doc_id = f"conv::{int(ts * 1000)}"
            document = f"User: {q}\nAssistant: {a}"
            metadata = {
                "type": "conversation",
                "timestamp": ts,
            }
            self.store.add_conversation(doc_id, document, metadata)
        except Exception as exc:  # pragma: no cover
            self.log.exception("Failed to store conversation: %s", exc)

