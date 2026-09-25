"""
API principal do Legacy Code Explainer.
Expõe endpoints para indexar um repositório, fazer perguntas e analisar
problemas de código legado. Também serve o frontend estático em "/".

Os repositórios são clonados em pastas temporárias do sistema operacional
(fora da pasta do projeto) e removidos automaticamente após o uso.
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.parser.git_loader import clone_repo, cleanup_repo
from src.parser.indexer import index_repository
from src.rag.engine import answer_question
from src.analysis.analyzer import analyze_repository
from src.rag.llm import synthesize_analysis

app = FastAPI(
    title="Legacy Code Explainer",
    description="Plataforma de IA para entender e modernizar sistemas Java Spring Boot legados.",
    version="0.4.0",
)

# Guarda a URL do último repositório indexado (não o path — a pasta é temporária
# e já foi apagada). O /analyze reclona temporariamente quando precisar.
_estado = {"ultima_repo_url": None}


class RepoRequest(BaseModel):
    url: str


class QuestionRequest(BaseModel):
    question: str


@app.get("/")
def root():
    """Serve o frontend (página HTML principal)."""
    return FileResponse("static/index.html")


@app.get("/api/status")
def status():
    return {"status": "ok", "service": "legacy-code-explainer"}


@app.post("/index")
def index_project(req: RepoRequest):
    """
    Clona o repositório numa pasta temporária, indexa seus arquivos relevantes
    no ChromaDB, e remove a pasta temporária logo em seguida.
    """
    repo_path = None
    try:
        repo_path = clone_repo(req.url)
        resumo = index_repository(repo_path)
        _estado["ultima_repo_url"] = req.url
        return {"status": "indexado", "resumo": resumo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cleanup_repo(repo_path)


@app.post("/ask")
def ask(req: QuestionRequest):
    """Responde uma pergunta sobre o projeto indexado (busca semântica + LLM)."""
    try:
        return answer_question(req.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
def analyze():
    """
    Analisa o último projeto indexado em busca de problemas comuns de código legado.
    Como a pasta clonada é temporária e já foi removida após o /index, este endpoint
    reclona o repositório momentaneamente, roda a análise, e remove a pasta de novo.
    """
    repo_url = _estado["ultima_repo_url"]
    if not repo_url:
        raise HTTPException(
            status_code=400,
            detail="Nenhum projeto foi indexado ainda. Chame /index primeiro.",
        )

    repo_path = None
    try:
        repo_path = clone_repo(repo_url)
        report = analyze_repository(repo_path)
        explicacao = synthesize_analysis(report)
        return {"relatorio_bruto": report, "explicacao": explicacao}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cleanup_repo(repo_path)


# Monta a pasta static para servir CSS/JS/imagens adicionais, se houver
app.mount("/static", StaticFiles(directory="static"), name="static")