"""
Heurísticas objetivas para detectar problemas comuns em código legado Java/Spring.
Cada função analisa o conteúdo de um arquivo e retorna uma lista de problemas
encontrados (sem usar LLM — é análise direta de texto/regex, rápida e confiável).
"""
import re

# Limites configuráveis
MAX_LINHAS_CLASSE = 300
MAX_METODOS_CLASSE = 20
MAX_DEPENDENCIAS_INJETADAS = 7


def _contar_linhas(content: str) -> int:
    return len(content.splitlines())


def check_god_class(content: str, metadata: dict) -> list[dict]:
    """Detecta classes muito grandes (candidatas a 'God Class')."""
    problemas = []
    linhas = _contar_linhas(content)
    if linhas > MAX_LINHAS_CLASSE:
        problemas.append({
            "categoria": "god_class",
            "severidade": "alta",
            "arquivo": metadata["arquivo"],
            "descricao": f"Classe com {linhas} linhas (limite recomendado: {MAX_LINHAS_CLASSE}). "
                         f"Pode estar fazendo responsabilidades demais.",
        })

    metodos = re.findall(r"(?:public|private|protected)\s+[\w<>\[\],\s]+\s+\w+\s*\([^)]*\)\s*\{", content)
    if len(metodos) > MAX_METODOS_CLASSE:
        problemas.append({
            "categoria": "god_class",
            "severidade": "media",
            "arquivo": metadata["arquivo"],
            "descricao": f"Classe com aproximadamente {len(metodos)} métodos (limite recomendado: {MAX_METODOS_CLASSE}).",
        })

    return problemas


def check_logica_em_controller(content: str, metadata: dict) -> list[dict]:
    """Detecta lógica de negócio (ex: SQL, regras condicionais complexas) direto no Controller."""
    problemas = []
    if metadata["tipo"] != "controller":
        return problemas

    if re.search(r"\b(SELECT|INSERT|UPDATE|DELETE)\b", content, re.IGNORECASE):
        problemas.append({
            "categoria": "logica_no_lugar_errado",
            "severidade": "alta",
            "arquivo": metadata["arquivo"],
            "descricao": "Controller parece conter SQL direto. O acesso a dados deveria "
                         "estar na camada de Repository.",
        })

    if_count = len(re.findall(r"\bif\s*\(", content))
    if if_count > 8:
        problemas.append({
            "categoria": "logica_no_lugar_errado",
            "severidade": "media",
            "arquivo": metadata["arquivo"],
            "descricao": f"Controller com {if_count} condicionais. Regras de negócio complexas "
                         f"deveriam estar na camada de Service.",
        })

    return problemas


def check_tratamento_erro_fraco(content: str, metadata: dict) -> list[dict]:
    """Detecta catch vazio ou genérico demais."""
    problemas = []

    catch_vazio = re.findall(r"catch\s*\([^)]*\)\s*\{\s*\}", content)
    if catch_vazio:
        problemas.append({
            "categoria": "tratamento_erro_fraco",
            "severidade": "alta",
            "arquivo": metadata["arquivo"],
            "descricao": f"{len(catch_vazio)} bloco(s) catch vazio(s) encontrado(s). "
                         f"Erros sendo silenciados sem log ou tratamento.",
        })

    catch_generico = re.findall(r"catch\s*\(\s*Exception\s+\w+\s*\)", content)
    if catch_generico:
        problemas.append({
            "categoria": "tratamento_erro_fraco",
            "severidade": "media",
            "arquivo": metadata["arquivo"],
            "descricao": f"{len(catch_generico)} catch(es) genérico(s) de 'Exception'. "
                         f"Recomenda-se capturar exceções específicas.",
        })

    return problemas


def check_padroes_antigos(content: str, metadata: dict) -> list[dict]:
    """Detecta padrões considerados antigos/desatualizados no Spring."""
    problemas = []

    if re.search(r"@Autowired\s*\n\s*(private|protected)\s+\w+\s+\w+;", content):
        problemas.append({
            "categoria": "padrao_antigo",
            "severidade": "baixa",
            "arquivo": metadata["arquivo"],
            "descricao": "Uso de @Autowired em campo (field injection). "
                         "Recomenda-se injeção via construtor para facilitar testes.",
        })

    if "extends HttpServlet" in content:
        problemas.append({
            "categoria": "padrao_antigo",
            "severidade": "media",
            "arquivo": metadata["arquivo"],
            "descricao": "Uso de Servlet clássico em vez de Spring MVC/RestController.",
        })

    return problemas


def check_entity_exposta(content: str, metadata: dict) -> list[dict]:
    """Detecta Controllers retornando Entities diretamente (sem DTO)."""
    problemas = []
    if metadata["tipo"] != "controller":
        return problemas

    if re.search(r"@Entity", content):
        problemas.append({
            "categoria": "sem_dto",
            "severidade": "media",
            "arquivo": metadata["arquivo"],
            "descricao": "Entity aparentemente usada diretamente no Controller. "
                         "Recomenda-se usar DTOs para não expor o modelo de dados interno na API.",
        })

    return problemas


def check_dependencias_excessivas(content: str, metadata: dict) -> list[dict]:
    """Detecta classes com muitas dependências injetadas (alto acoplamento)."""
    problemas = []

    injecoes = re.findall(r"@Autowired|private\s+final\s+\w+\s+\w+;", content)
    if len(injecoes) > MAX_DEPENDENCIAS_INJETADAS:
        problemas.append({
            "categoria": "alto_acoplamento",
            "severidade": "media",
            "arquivo": metadata["arquivo"],
            "descricao": f"Aproximadamente {len(injecoes)} dependências injetadas. "
                         f"Alto acoplamento pode indicar que a classe faz responsabilidades demais.",
        })

    return problemas


# Lista de todas as heurísticas a aplicar em cada arquivo Java
ALL_CHECKS = [
    check_god_class,
    check_logica_em_controller,
    check_tratamento_erro_fraco,
    check_padroes_antigos,
    check_entity_exposta,
    check_dependencias_excessivas,
]


def run_all_checks(content: str, metadata: dict) -> list[dict]:
    """Roda todas as heurísticas em um arquivo e retorna a lista consolidada de problemas."""
    problemas = []
    for check in ALL_CHECKS:
        problemas.extend(check(content, metadata))
    return problemas