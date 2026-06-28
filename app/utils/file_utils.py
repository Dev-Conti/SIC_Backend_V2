import os
import csv
import json

def load_file(file_name, folder="queries/sql_server"):
    """Carrega o conteúdo de um arquivo dado o nome e a pasta"""

    # Obtém o diretório onde o script file_utils.py está localizado
    base_path = os.path.dirname(os.path.abspath(__file__))  # Diretório de utils/file_utils.py

    # Ajuste: Agora vamos adicionar o caminho do diretório 'app'
    app_path = os.path.dirname(base_path)  # Um nível acima de utils
    file_path = os.path.join(app_path, folder, file_name)  # Combina o caminho com a pasta e o nome do arquivo

    # Verifica se o arquivo existe no caminho calculado
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo {file_name} não encontrado na pasta {folder}")
    
    # Abre e retorna o conteúdo do arquivo
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def load_csv(file_name, folder="data"):
    """Carrega dados de um arquivo CSV"""
    file_path = os.path.join(os.path.dirname(__file__), folder, file_name)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo {file_name} não encontrado na pasta {folder}")

    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            data.append(row)
    return data

def save_json(data, file_name, folder="data"):
    """Salva dados em um arquivo JSON"""
    # Obtém o diretório onde o script file_utils.py está localizado
    base_path = os.path.dirname(os.path.abspath(__file__))  # Diretório de utils/file_utils.py

    # Ajuste: Agora vamos adicionar o caminho do diretório 'app'
    app_path = os.path.dirname(base_path)  # Um nível acima de utils
    file_path = os.path.join(app_path, folder, file_name)  # Combina o caminho com a pasta e o nome do arquivo

    # Cria a pasta se ela não existir
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Salva os dados no arquivo JSON
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)