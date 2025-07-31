import os
import shutil

def find_large_files(folder, limit_mb):
    result = []
    for root, _, files in os.walk(folder):
        for file in files:
            path = os.path.join(root, file)
            try:
                size = os.path.getsize(path)
                if size >= limit_mb * 1024 * 1024:
                    result.append((path, size))
            except Exception as e:
                print(f"Erro ao acessar {path}: {e}")
    return sorted(result, key=lambda x: x[1], reverse=True)

def excluir_arquivos(arquivos):
    erros = []
    for path in arquivos:
        try:
            if os.path.isfile(path):
                os.remove(path)
        except Exception as e:
            erros.append((path, str(e)))
    return erros

def mover_arquivos(arquivos, destino):
    erros = []
    for path in arquivos:
        try:
            shutil.move(path, destino)
        except Exception as e:
            erros.append((path, str(e)))
    return erros
