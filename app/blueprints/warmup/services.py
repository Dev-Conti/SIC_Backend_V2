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

def _tem_secao(dados):
    """Indica se o payload traz alguma seção (valor dict não vazio) a mesclar."""
    return any("." not in campo and isinstance(valor, dict) and valor for campo, valor in dados.items())

def montar_set_parcial(dados, documento_atual=None):
    """Converte o payload de atualização nas operações do $set.

    Seções (chaves de topo com valor dict) são achatadas um nível, em
    "secao.chave", para que chaves não enviadas não sejam apagadas; cada
    chave enviada substitui seu valor por inteiro. Seção vazia não gera
    operação. Chaves já em dot-notation passam direto e têm precedência.
    Se a seção atual no documento não for um dict (ausente/None/escalar),
    ela é gravada inteira, pois o Mongo não cria subcampo sob um não-objeto.
    """
    set_fields = {}
    secoes_inteiras = {}
    explicitos = {}

    for campo, valor in dados.items():
        if "." in campo:
            explicitos[campo] = valor
        elif isinstance(valor, dict):
            if not valor:
                continue
            atual = documento_atual.get(campo) if documento_atual else None
            if isinstance(atual, dict):
                for chave, sub_valor in valor.items():
                    set_fields[f"{campo}.{chave}"] = sub_valor
            else:
                secoes_inteiras[campo] = dict(valor)
        else:
            set_fields[campo] = valor

    # Chave explícita dentro de uma seção gravada inteira entra no próprio
    # objeto, evitando conflito "secao" x "secao.chave" no mesmo $set.
    for caminho, valor in explicitos.items():
        raiz, resto = caminho.split(".", 1)
        if raiz in secoes_inteiras:
            alvo = secoes_inteiras[raiz]
            *intermediarios, ultimo = resto.split(".")
            for parte in intermediarios:
                if not isinstance(alvo.get(parte), dict):
                    alvo[parte] = {}
                else:
                    alvo[parte] = dict(alvo[parte])
                alvo = alvo[parte]
            alvo[ultimo] = valor
        else:
            set_fields[caminho] = valor

    set_fields.update(secoes_inteiras)
    return set_fields

def atualizar_warmup(negocio_id, dados):
    """Atualiza um documento na coleção warmup_projetos pelo ID.

    Seções enviadas são mescladas (ver montar_set_parcial): chaves não
    enviadas são preservadas, para que o salvamento de uma etapa não apague
    dados preenchidos por outra.
    """
    query = {"negocio_id": negocio_id}

    novo_status = dados.get("status")
    documento_atual = None
    if novo_status is not None or _tem_secao(dados):
        documento_atual = mongo.db.warmup_projetos.find_one(query)

    set_fields = montar_set_parcial(dados, documento_atual)
    if not set_fields:
        return 0
    update = {"$set": set_fields}

    if novo_status is not None:
        status_atual = documento_atual.get("status") if documento_atual else None
        if novo_status != status_atual:
            entrada_historico = {
                "status": novo_status,
                "etapa": dados.get("etapa", documento_atual.get("etapa") if documento_atual else None),
                "alterado_em": datetime.utcnow(),
            }

            observacao = dados.get("observacao")
            if observacao:
                entrada_historico["observacao"] = observacao
                if dados.get("usuario"):
                    entrada_historico["usuario"] = dados.get("usuario")

            update["$push"] = {"status_historico": entrada_historico}

    resultado = mongo.db.warmup_projetos.update_one(query, update)
    return resultado.modified_count


