"""
Motor RAG: recebe uma pergunta, decide a melhor estratégia de resposta
(listagem direta por metadados, extração de endpoints, ou busca semântica),
recupera o contexto necessário e envia para o LLM local responder.
"""
import re

from src.embeddings.embedder import embed_texts
from src.retrieval.vector_store import query, get_all_documents
from src.rag.llm import ask_llm

# Palavras-chave que indicam que o usuário quer uma LISTAGEM COMPLETA,
# não uma busca por similaridade (que poderia deixar itens de fora).
PALAVRAS_LISTAGEM = [
    "quais", "liste", "listar", "todos", "todas", "quantos", "quantas",
    "mostre todos", "mostrar todos",
]

TIPO_POR_PALAVRA = {
    "controller": "controller",
    "controllers": "controller",
    "service": "service",
    "services": "service",
    "repository": "repository",
    "repositories": "repository",
    "entity": "entity",
    "entities": "entity",
    "dto": "dto",
    "dtos": "dto",
    "endpoint": "endpoint",
    "endpoints": "endpoint",
    "rota": "endpoint",
    "rotas": "endpoint",
}

MAPPING_ANNOTATIONS = re.compile(
    r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)'
    r'(?:\s*\(\s*(?:value\s*=\s*)?"([^"]*)"[^)]*\))?'
)


def _detectar_intencao(question: str) -> str | None:
    """
    Analisa a pergunta e decide se é uma listagem (por tipo específico,
    endpoints, ou nenhuma das duas -> busca semântica normal).
    Retorna: 'endpoint', um tipo (ex: 'controller'), ou None.
    """
    q_lower = question.lower()

    tem_palavra_listagem = any(p in q_lower for p in PALAVRAS_LISTAGEM)
    if not tem_palavra_listagem:
        return None

    for palavra, tipo in TIPO_POR_PALAVRA.items():
        if palavra in q_lower:
            return tipo

    return None


def _listar_por_tipo(tipo: str) -> dict:
    """Retorna todos os arquivos indexados de um tipo específico, direto dos metadados."""
    dados = get_all_documents()
    metadatas = dados.get("metadatas", [])

    itens = [m for m in metadatas if m.get("tipo") == tipo]

    if not itens:
        return {
            "answer": f"Não foi encontrado nenhum arquivo do tipo '{tipo}' no projeto indexado.",
            "fontes": [],
        }

    linhas = [f"- **{m.get('classe', m.get('arquivo'))}** (pacote: `{m.get('pacote', 'N/A')}`)" for m in itens]
    resposta = f"Encontrei {len(itens)} classe(s) do tipo '{tipo}':\n\n" + "\n".join(linhas)

    fontes = [{"arquivo": m.get("arquivo"), "tipo": m.get("tipo")} for m in itens]
    return {"answer": resposta, "fontes": fontes}


def _extrair_endpoints() -> dict:
    """
    Varre todos os controllers indexados e extrai os endpoints reais
    via regex nas anotações do Spring (@GetMapping, @PostMapping, etc),
    em vez de confiar no LLM para 'adivinhar' pelo texto.
    """
    dados = get_all_documents()
    documentos = dados.get("documents", [])
    metadatas = dados.get("metadatas", [])

    endpoints_encontrados = []

    for doc, meta in zip(documentos, metadatas):
        if meta.get("tipo") != "controller":
            continue

        # Pega o prefixo de rota do @RequestMapping a nível de classe, se existir
        base_path_match = re.search(r'@RequestMapping\s*\(\s*(?:value\s*=\s*)?"([^"]*)"', doc)
        base_path = base_path_match.group(1) if base_path_match else ""

        for match in MAPPING_ANNOTATIONS.finditer(doc):
            metodo_http = match.group(1).replace("Mapping", "").upper()
            if metodo_http == "REQUEST":
                metodo_http = "REQUEST (verbo não especificado)"
            path = match.group(2) or ""
            caminho_completo = (base_path.rstrip("/") + "/" + path.lstrip("/")).rstrip("/")
            if not caminho_completo:
                caminho_completo = "/"

            endpoints_encontrados.append({
                "metodo": metodo_http,
                "path": caminho_completo,
                "classe": meta.get("classe", meta.get("arquivo")),
            })

    if not endpoints_encontrados:
        return {
            "answer": "Não foram encontrados endpoints (anotações @GetMapping, @PostMapping etc) "
                      "nos controllers indexados.",
            "fontes": [],
        }

    linhas = [f"- `{e['metodo']} {e['path']}` → {e['classe']}" for e in endpoints_encontrados]
    resposta = f"Encontrei {len(endpoints_encontrados)} endpoint(s):\n\n" + "\n".join(linhas)

    fontes = [{"arquivo": e["classe"], "tipo": "controller"} for e in endpoints_encontrados]
    return {"answer": resposta, "fontes": fontes}


def _resposta_semantica(question: str, n_results: int = 5) -> dict:
    """Fluxo original: busca por similaridade + LLM. Usado para perguntas explicativas."""
    q_embedding = embed_texts([question])[0]
    results = query(q_embedding, n_results=n_results)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    if not documents:
        return {
            "answer": "Nenhum contexto relevante foi encontrado. O projeto foi indexado?",
            "fontes": [],
        }

    context_parts = []
    fontes = []
    for doc, meta in zip(documents, metadatas):
        context_parts.append(f"### {meta.get('arquivo')} ({meta.get('tipo')})\n{doc}")
        fontes.append({"arquivo": meta.get("arquivo"), "tipo": meta.get("tipo")})

    context = "\n\n".join(context_parts)
    answer = ask_llm(question, context)

    return {"answer": answer, "fontes": fontes}


def answer_question(question: str, n_results: int = 5) -> dict:
    """
    Ponto de entrada principal. Decide a estratégia certa antes de responder:
    - Pergunta sobre endpoints -> extração real via regex nas anotações
    - Pergunta de listagem por tipo (controllers, services, etc) -> metadados diretos
    - Qualquer outra pergunta -> busca semântica + LLM (fluxo original)
    """
    intencao = _detectar_intencao(question)

    if intencao == "endpoint":
        return _extrair_endpoints()

    if intencao is not None:
        return _listar_por_tipo(intencao)

    return _resposta_semantica(question, n_results=n_results)