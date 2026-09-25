
#Varredura de arquivos do projeto e classificação de classes Java (controller, service, repository, entity, dto, config)
import os
import re

IGNORE_DIRS = {"target", ".git", ".idea", "node_modules", "build", ".mvn"}
VALID_EXT = {".java", ".yml", ".yaml", ".properties", ".md"}


def list_relevant_files(root: str) -> list[str]:
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for f in filenames:
            if os.path.splitext(f)[1] in VALID_EXT:
                files.append(os.path.join(dirpath, f))
    return files


def classify_java_file(filepath: str, content: str) -> dict:

    filename = os.path.basename(filepath)
    tipo = "unknown"

    if "@RestController" in content or "@Controller" in content:
        tipo = "controller"
    elif "@Service" in content:
        tipo = "service"
    elif "@Repository" in content:
        tipo = "repository"
    elif "@Entity" in content:
        tipo = "entity"
    elif filename.endswith("DTO.java") or filename.endswith("Dto.java"):
        tipo = "dto"
    elif "@Configuration" in content:
        tipo = "config"

    pacote_match = re.search(r"package\s+([\w.]+);", content)
    pacote = pacote_match.group(1) if pacote_match else ""

    classe_match = re.search(r"(?:class|interface|enum)\s+(\w+)", content)
    nome_classe = classe_match.group(1) if classe_match else filename.replace(".java", "")

    return {
        "arquivo": filename,
        "classe": nome_classe,
        "tipo": tipo,
        "pacote": pacote,
        "path": filepath,
    }


def classify_config_file(filepath: str) -> dict:
    filename = os.path.basename(filepath)
    ext = os.path.splitext(filename)[1]
    tipo_map = {
        ".yml": "config",
        ".yaml": "config",
        ".properties": "config",
        ".md": "documentacao",
    }
    return {
        "arquivo": filename,
        "classe": filename,
        "tipo": tipo_map.get(ext, "outro"),
        "pacote": "",
        "path": filepath,
    }