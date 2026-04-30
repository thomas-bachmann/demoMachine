import os
import sys
from pathlib import Path
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.node_parser import CodeSplitter, SentenceSplitter
from llama_index.core import Document
from rag import get_settings, STORAGE_DIR

SOURCE_DIRS = {
    "backend": "/app_source/backend",
    "frontend": "/app_source/frontend/src",
    "mcp": "/app_source/mcp",
}

EXTENSIONS = {
    ".py":   "python",
    ".vue":  "text",   # pas supporté par Tree-sitter, fallback texte
    ".js":   "javascript",
    ".md":   "text",
}

def load_documents():
    docs = []
    for zone, path in SOURCE_DIRS.items():
        for ext, lang in EXTENSIONS.items():
            files = list(Path(path).rglob(f"*{ext}"))
            if not files:
                continue

            reader = SimpleDirectoryReader(
                input_files=[str(f) for f in files],
                file_metadata=lambda p: {
                    "zone": zone,
                    "filename": Path(p).name,
                    "filepath": str(p),
                }
            )
            docs.extend(reader.load_data())
            print(f"  {zone}{ext}: {len(files)} fichier(s)")
    return docs

def get_splitter(doc):
    ext = Path(doc.metadata.get("filename", "")).suffix
    lang = EXTENSIONS.get(ext)
    if lang in ("python", "javascript"):
        return CodeSplitter(language=lang, chunk_lines=40, chunk_lines_overlap=5)
    return SentenceSplitter(chunk_size=512, chunk_overlap=50)

def main():
    get_settings()
    print("Chargement des fichiers...")
    docs = load_documents()
    print(f"Total: {len(docs)} document(s)")

    print("Découpage et indexation...")
    nodes = []
    for doc in docs:
        splitter = get_splitter(doc)
        nodes.extend(splitter.get_nodes_from_documents([doc]))

    index = VectorStoreIndex(nodes, show_progress=True)
    index.storage_context.persist(persist_dir=STORAGE_DIR)
    print(f"Index sauvegardé dans {STORAGE_DIR}")

if __name__ == "__main__":
    main()