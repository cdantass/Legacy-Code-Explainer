"""
Armazenamento e recuperação de documentos indexados no ChromaDB.
"""
import chromadb

_client = None
_collection = None


def get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path="chroma_db")
        _collection = _client.get_or_create_collection("legacy_code")
    return _collection


def reset_collection():
    """Apaga e recria a coleção (útil ao reindexar um projeto do zero)."""
    global _client, _collection
    if _client is None:
        _client = chromadb.PersistentClient(path="chroma_db")
    try:
        _client.delete_collection("legacy_code")
    except Exception:
        pass
    _collection = _client.get_or_create_collection("legacy_code")
    return _collection


def index_file(doc_id: str, content: str, embedding: list, metadata: dict):
    collection = get_collection()
    collection.add(
        ids=[doc_id],
        embeddings=[embedding],
        documents=[content],
        metadatas=[metadata],
    )


def query(embedding: list, n_results: int = 5):
    collection = get_collection()
    return collection.query(query_embeddings=[embedding], n_results=n_results)


def get_all_documents(limit: int = 5000):
    """
    Retorna todos os documentos e metadados indexados, sem busca semântica.
    Usado para perguntas do tipo 'liste todos os X' ou 'quantos Y existem',
    onde a busca por similaridade não é confiável (pode deixar itens de fora).
    """
    collection = get_collection()
    return collection.get(limit=limit, include=["documents", "metadatas"])