"""
Integração com o modelo LLM local via Ollama.
"""
import json
import ollama

SYSTEM_PROMPT = """Você é um assistente especialista em sistemas Java Spring Boot.
Sua função é explicar arquitetura, fluxos de negócio e dependências de um sistema legado.
Use APENAS as informações fornecidas no contexto abaixo para responder.
Se a resposta não estiver no contexto, diga claramente que não encontrou essa informação
no código analisado, em vez de inventar uma resposta.
Sempre que possível, cite os nomes exatos das classes envolvidas."""


ANALYSIS_SYSTEM_PROMPT = """Você é um arquiteto de software sênior especializado em
modernização de sistemas Java Spring Boot legados.

Você vai receber um relatório técnico bruto, gerado por análise automática de código,
contendo uma lista de problemas encontrados (categoria, severidade, arquivo, descrição).

Sua tarefa é transformar esse relatório em uma explicação clara e priorizada para o
desenvolvedor, seguindo estas regras:

1. Comece com um resumo geral (quantos problemas, principais categorias).
2. Liste os problemas de severidade ALTA primeiro, depois MÉDIA, depois BAIXA.
3. Para cada problema, explique em 1-2 frases o RISCO real que ele representa
   (não apenas repita a descrição técnica).
4. Sugira uma recomendação prática e objetiva de como resolver.
5. Ao final, dê uma recomendação de "por onde começar" considerando impacto x esforço.
6. Use apenas as informações do relatório. Não invente arquivos ou problemas que não
   estão na lista.
7. Seja direto e técnico, evite enrolação."""


def ask_llm(question: str, context: str, model: str = "llama3.1:8b") -> str:
    prompt = f"""Contexto (trechos de código relevantes):

{context}

Pergunta: {question}

Resposta:"""

    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return response["message"]["content"]


def synthesize_analysis(report: dict, model: str = "llama3.1:8b") -> str:
    """
    Recebe o relatório estruturado gerado pelo analyzer.py e pede pro LLM
    transformar em uma explicação priorizada e legível para o desenvolvedor.
    """
    relatorio_json = json.dumps(report, ensure_ascii=False, indent=2)

    prompt = f"""Relatório técnico de análise do projeto:

{relatorio_json}

Gere a explicação priorizada seguindo as regras do sistema."""

    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return response["message"]["content"]