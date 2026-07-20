from app.config import Config
from app.extensions import mongo
import requests
from bson import ObjectId
from datetime import datetime

def get_warmup_projetos_collection(etapa=None):
    """Retorna a coleção warmup_projetos do MongoDB.
    
    Se o parâmetro etapa for fornecido, retorna apenas os documentos correspondentes.
    """
    query = {}
    if etapa is not None:
        query['etapa'] = etapa

    dados = mongo.db.warmup_projetos.find(query)
    return list(dados)  # Converter cursor para lista e retornar

def get_warmup_projeto_by_id(negocio_id):
    """Retorna um único documento da coleção warmup_projetos pelo ID."""
    document = mongo.db.warmup_projetos.find_one({"negocio_id": negocio_id})
    return document

def iniciar_warmup(dados):
    """Processa e insere dados na coleção warmup_projetos."""
    responsavel_nome = dados.get("responsavel", "")
    responsavel_email = dados.get("email_responsavel", "")

    if not responsavel_nome or not responsavel_email:
        raise ValueError("Nome e email do responsável comercial são obrigatórios.")

    agora = datetime.utcnow()
    etapa_inicial = "Warmup Comercial"
    status_inicial = "Aguardando"

    dados_insert = {
        "negocio_id": dados.get("negocio_id", ""),
        "etapa": etapa_inicial,
        "status": status_inicial,
        "inicio_warmup": agora,
        "status_historico": [
            {
                "status": status_inicial,
                "etapa": etapa_inicial,
                "alterado_em": agora,
            }
        ],
        "cliente": {
            "nome": dados.get("cliente_nome", ""),
            "cliente_id": dados.get("cliente_id", "")
        },
        "capa_projeto": {
            "codigo": dados.get("codigo_projeto", ""),
            "nome_vendedor": dados.get('nome_vendedor'),
            "email_vendedor": dados.get('email_vendedor')
        },
        "formacao_preco": {
            "valor": dados.get("valor", ""),
        },
        "cronograma_execucao": {},
        "adicionais_projeto": {},
        "faturamento": {},
        "observacoes_gerais": [],
        "responsaveis": {
            "responsavel_comercial": {
                "nome": responsavel_nome,
                "email": responsavel_email
            }
        }
    }

    collection = mongo.db.warmup_projetos
    resultado = collection.insert_one(dados_insert)
    return str(resultado.inserted_id)

def atualizar_warmup(negocio_id, dados):
    """Atualiza um documento na coleção warmup_projetos pelo ID."""
    query = {"negocio_id": negocio_id}
    update = {"$set": dados}

    novo_status = dados.get("status")
    if novo_status is not None:
        documento_atual = mongo.db.warmup_projetos.find_one(query)
        status_atual = documento_atual.get("status") if documento_atual else None
        if novo_status != status_atual:
            update["$push"] = {
                "status_historico": {
                    "status": novo_status,
                    "etapa": dados.get("etapa", documento_atual.get("etapa") if documento_atual else None),
                    "alterado_em": datetime.utcnow(),
                }
            }

    resultado = mongo.db.warmup_projetos.update_one(query, update)
    return resultado.modified_count


