"""
Orquestra a análise completa de um repositório: percorre todos os arquivos
Java já classificados, roda as heurísticas de detecção de problemas e
consolida um relatório estruturado.
"""
import os

from src.parser.file_scanner import list_relevant_files, classify_java_file
from src.analysis.heuristics import run_all_checks


def analyze_repository(repo_path: str) -> dict:
    """
    Varre o repositório, roda as heurísticas em cada arquivo .java
    e retorna um relatório consolidado com todos os problemas encontrados.
    """
    files = list_relevant_files(repo_path)
    todos_problemas = []
    arquivos_analisados = 0

    for filepath in files:
        if not filepath.endswith(".java"):
            continue

        try:
            with open(filepath, encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            print(f"[aviso] Não foi possível ler {filepath}: {e}")
            continue

        if not content.strip():
            continue

        metadata = classify_java_file(filepath, content)
        problemas = run_all_checks(content, metadata)
        todos_problemas.extend(problemas)
        arquivos_analisados += 1

    # Verifica se existe pasta de testes (heurística simples de "falta de testes")
    tem_testes = _verificar_testes(repo_path)
    if not tem_testes:
        todos_problemas.append({
            "categoria": "falta_de_testes",
            "severidade": "alta",
            "arquivo": "(projeto inteiro)",
            "descricao": "Não foi encontrada uma pasta de testes (src/test) com "
                         "arquivos de teste significativos no projeto.",
        })

    resumo_por_categoria = _agrupar_por_categoria(todos_problemas)
    resumo_por_severidade = _agrupar_por_severidade(todos_problemas)

    return {
        "arquivos_analisados": arquivos_analisados,
        "total_problemas": len(todos_problemas),
        "por_categoria": resumo_por_categoria,
        "por_severidade": resumo_por_severidade,
        "problemas": todos_problemas,
    }


def _verificar_testes(repo_path: str) -> bool:
    """Verifica se existe uma pasta de testes com pelo menos um arquivo .java dentro."""
    for dirpath, dirnames, filenames in os.walk(repo_path):
        if os.path.basename(dirpath) == "test":
            java_tests = [f for f in filenames if f.endswith(".java")]
            if java_tests:
                return True
    return False


def _agrupar_por_categoria(problemas: list[dict]) -> dict:
    resumo = {}
    for p in problemas:
        cat = p["categoria"]
        resumo[cat] = resumo.get(cat, 0) + 1
    return resumo


def _agrupar_por_severidade(problemas: list[dict]) -> dict:
    resumo = {}
    for p in problemas:
        sev = p["severidade"]
        resumo[sev] = resumo.get(sev, 0) + 1
    return resumo