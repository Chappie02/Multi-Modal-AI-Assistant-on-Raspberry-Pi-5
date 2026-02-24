import logging
from typing import Generator

try:
    from llama_cpp import Llama
except Exception:  # pragma: no cover
    Llama = None


class LlmChat:
    """
    Offline LLM chat using llama.cpp bindings.
    Loads GGUF model from models/llm.gguf.
    """

    def __init__(self, model_path: str = "models/gemma-3-4b-it-IQ4_XS.gguf") -> None:
        self.log = logging.getLogger("llm")
        self._llm = None
        try:
            if Llama is None:
                raise RuntimeError("llama_cpp is not installed.")
            self._llm = Llama(
                model_path=model_path,
                n_ctx=2048,
                n_threads=4,
                embedding=False,
            )
        except Exception as e:
            self.log.exception("Failed to load LLM model: %s", e)

    def stream_chat(
        self,
        prompt: str,
        context_chunks: "list[str] | None" = None,
    ) -> Generator[str, None, None]:
        """
        Stateless single-turn chat.
        Streams tokens as they are generated.
        """
        if self._llm is None:
            self.log.error("LLM not available.")
            return

        try:
            # When RAG supplies context chunks, build an augmented prompt
            # that follows the requested SYSTEM / CONTEXT / USER structure.
            if context_chunks:
                context_text = "\n\n".join(context_chunks)
                full_prompt = (
                    "SYSTEM:\n"
                    "Use the provided context to answer clearly. "
                    "If context is insufficient, answer normally.\n\n"
                    "CONTEXT:\n"
                    f"{context_text}\n\n"
                    "USER:\n"
                    f"{prompt}\n\n"
                    "ASSISTANT:"
                )
            else:
                # Fallback to the original concise, stateless prompt.
                full_prompt = (
                    "You are a concise helpful assistant running fully offline on a "
                    "small device. Answer briefly.\n\nUser: "
                    + prompt
                    + "\nAssistant:"
                )

            for token in self._llm(
                full_prompt,
                max_tokens=256,
                stop=["User:", "Assistant:"],
                stream=True,
            ):
                try:
                    part = token.get("choices", [{}])[0].get("text", "")
                except Exception:
                    part = ""
                if part:
                    yield part
        except Exception:
            self.log.exception("LLM streaming failed.")
            return

