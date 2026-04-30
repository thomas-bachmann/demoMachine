import os
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage, Settings
from llama_index.llms.litellm import LiteLLM
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

STORAGE_DIR = "/index_storage"

def get_settings():
    Settings.llm = LiteLLM(
        model=os.getenv("LLM_MODEL", "claude-haiku-4-5-20251001")
    )
    Settings.embed_model = HuggingFaceEmbedding(
        model_name="BAAI/bge-small-en-v1.5"
    )

def load_query_engine():
    get_settings()
    storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
    index = load_index_from_storage(storage_context)
    return index.as_query_engine(similarity_top_k=5)

_query_engine = None

def get_query_engine():
    global _query_engine
    if _query_engine is None:
        try:
            _query_engine = load_query_engine()
        except Exception as e:
            raise RuntimeError(f"Index non disponible. Lance 'make index' d'abord. ({e})")
    return _query_engine