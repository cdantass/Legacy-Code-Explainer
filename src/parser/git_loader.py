"""
Responsável por clonar repositórios Git para análise local, usando uma
pasta temporária do sistema operacional (fora da pasta do projeto).
"""
from git import Repo
import shutil
import stat
import tempfile
import os


def _remover_readonly(func, path, exc_info):
    """
    Callback usado pelo shutil.rmtree para lidar com arquivos somente-leitura
    no Windows (comum em arquivos dentro de .git/objects).
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)


def clone_repo(url: str) -> str:
    """
    Clona um repositório Git para uma pasta temporária do sistema
    (ex: C:\\Users\\voce\\AppData\\Local\\Temp\\lce_xxxxxxxx no Windows).
    Retorna o path da pasta clonada.
    """
    temp_dir = tempfile.mkdtemp(prefix="lce_")
    repo_name = url.rstrip("/").split("/")[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    path = os.path.join(temp_dir, repo_name)
    Repo.clone_from(url, path)

    return path


def cleanup_repo(path: str):
    """
    Remove a pasta clonada (e sua pasta temporária pai) após o uso,
    lidando com arquivos somente-leitura do Git no Windows.
    """
    if not path or not os.path.exists(path):
        return

    temp_parent = os.path.dirname(path)  # a pasta lce_xxxxxxxx criada pelo mkdtemp

    try:
        shutil.rmtree(temp_parent, onerror=_remover_readonly)
    except Exception as e:
        print(f"[aviso] Não foi possível limpar a pasta temporária {temp_parent}: {e}")