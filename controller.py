import os
import shutil

def validate_path(path):
    """
    Valida se o caminho existe e é acessível.
    Retorna (is_valid, error_message)
    """
    if not path or path.strip() == "":
        return False, "Caminho não pode estar vazio"
    
    if not os.path.exists(path):
        return False, "Caminho não existe"
    
    if not os.path.isdir(path):
        return False, "Caminho não é um diretório válido"
    
    if not os.access(path, os.R_OK):
        return False, "Sem permissão de leitura no diretório"
    
    return True, ""

def validate_file_permissions(files):
    """
    Valida se os arquivos podem ser modificados/excluídos.
    Retorna lista de arquivos com problemas.
    """
    problematic_files = []
    for file_path in files:
        if not os.path.exists(file_path):
            problematic_files.append((file_path, "Arquivo não existe"))
        elif not os.access(file_path, os.W_OK):
            problematic_files.append((file_path, "Sem permissão de escrita"))
        elif not os.access(os.path.dirname(file_path), os.W_OK):
            problematic_files.append((file_path, "Sem permissão no diretório pai"))
    
    return problematic_files

def validate_size_limit(limit_mb):
    """
    Valida se o limite de tamanho é válido.
    Retorna (is_valid, error_message)
    """
    try:
        limit = float(limit_mb)
        if limit <= 0:
            return False, "O tamanho deve ser maior que zero"
        if limit > 10000:  # Limite máximo de 10GB para evitar problemas
            return False, "Tamanho muito grande (máximo 10GB)"
        return True, ""
    except (ValueError, TypeError):
        return False, "Digite um número válido"

def find_large_files(folder, limit_mb):
    """
    Encontra arquivos grandes em uma pasta.
    Agora com validação de entrada.
    """
    # Validar pasta
    is_valid, error_msg = validate_path(folder)
    if not is_valid:
        raise ValueError(f"Erro na pasta: {error_msg}")
    
    # Validar limite
    is_valid, error_msg = validate_size_limit(limit_mb)
    if not is_valid:
        raise ValueError(f"Erro no limite de tamanho: {error_msg}")
    
    result = []
    limit_bytes = float(limit_mb) * 1024 * 1024
    
    for root, _, files in os.walk(folder):
        for file in files:
            path = os.path.join(root, file)
            try:
                size = os.path.getsize(path)
                if size >= limit_bytes:
                    result.append((path, size))
            except (OSError, PermissionError) as e:
                print(f"Erro ao acessar {path}: {e}")
    
    return sorted(result, key=lambda x: x[1], reverse=True)

def excluir_arquivos(arquivos):
    """
    Exclui arquivos com validação prévia de permissões.
    """
    # Validar permissões antes de tentar excluir
    problematic_files = validate_file_permissions(arquivos)
    if problematic_files:
        return problematic_files
    
    erros = []
    for path in arquivos:
        try:
            if os.path.isfile(path):
                os.remove(path)
        except Exception as e:
            erros.append((path, str(e)))
    return erros

def mover_arquivos(arquivos, destino):
    """
    Move arquivos com validação de destino e permissões.
    """
    # Validar destino
    is_valid, error_msg = validate_path(destino)
    if not is_valid:
        return [(destino, f"Erro no destino: {error_msg}")]
    
    # Validar permissões dos arquivos
    problematic_files = validate_file_permissions(arquivos)
    if problematic_files:
        return problematic_files
    
    # Verificar se destino tem permissão de escrita
    if not os.access(destino, os.W_OK):
        return [(destino, "Sem permissão de escrita no destino")]
    
    erros = []
    for path in arquivos:
        try:
            shutil.move(path, destino)
        except Exception as e:
            erros.append((path, str(e)))
    return erros
