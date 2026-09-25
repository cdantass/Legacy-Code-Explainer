# Orquestra a leitura, classificação, geração de embeddings e indexação de todos os arquivos relevantes de um repositório.

from src.parser.file_scanner import (
    list_relevant_files,
    classify_java_file,
    classify_config_file,
)
from src.embeddings.embedder import embed_texts
from src.retrieval.vector_store import index_file, reset_collection


def index_repository(repo_path: str) -> dict:
    """
    Lê todos os arquivos relevantes do repositório, classifica,
    gera embeddings e indexa no ChromaDB.
    Retorna um resumo do que foi indexado.
    """
    reset_collection()  # garante reindexação limpa a cada novo projeto

    files = list_relevant_files(repo_path)
    resumo = {"total_arquivos": 0, "por_tipo": {}}

    for filepath in files:
        try:
            with open(filepath, encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            print(f"[aviso] Não foi possível ler {filepath}: {e}")
            continue

        if not content.strip():
            continue

        if filepath.endswith(".java"):
            metadata = classify_java_file(filepath, content)
        else:
            metadata = classify_config_file(filepath)

        embedding = embed_texts([content])[0]
        index_file(doc_id=filepath, content=content, embedding=embedding, metadata=metadata)

        resumo["total_arquivos"] += 1
        tipo = metadata["tipo"]
        resumo["por_tipo"][tipo] = resumo["por_tipo"].get(tipo, 0) + 1

    return resumo