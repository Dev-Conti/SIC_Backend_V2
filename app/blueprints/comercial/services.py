from app.extensions import mongo
import requests
import pandas as pd
import json
import os
from pymongo import MongoClient
from app.config import Config
from app.blueprints.rdstation.services import RdServices, export_deals
from app.blueprints.warmup.services import (
    atualizar_warmup as atualizar_warmup_projeto,
    get_warmup_projetos_collection,
)
from app.utils.responses import success_response, error_response
from app.utils.datetime_util import DatetimeServices
from flask import current_app
from datetime import datetime, timedelta


def atualizar_negociacoes():
    """
    Atualiza ou insere negociações na coleção MongoDB a partir dos dados exportados.
    """
    # Obter negociações exportadas
    negociacoes = export_deals()

    if negociacoes is None:
        return error_response("Erro ao obter negociações.")

    operacoes = []
    for negociacao in negociacoes:
        filtro = {"_id": negociacao.get("_id")}  # Usar o campo único do MongoDB para identificar
        operacao = {
            "$set": negociacao  # Atualizar todos os campos do documento
        }
        operacoes.append((filtro, operacao))

    # Atualizar ou inserir cada negociação
    for filtro, update in operacoes:
        mongo.db.negociacoes.update_one(filtro, update, upsert=True)

    return success_response(f"{len(operacoes)} negociações atualizadas ou inseridas no MongoDB.", {"total": len(operacoes)})

def _documento_ganho(win):
    """Monta o documento padrão de warmup_projetos (etapa 'Ganhos') a partir de
    uma negociação ganha do RD Station, no mesmo formato usado pelas demais
    etapas do pipeline."""
    agora = datetime.utcnow()
    etapa_inicial = "Ganhos"
    status_inicial = "Aguardando"
    organization = win.get("organization") or {}
    user = win.get("user") or {}

    return {
        "negocio_id": win.get("id"),
        "etapa": etapa_inicial,
        "status": status_inicial,
        "ganho_em": agora,
        "rd_closed_at": win.get("closed_at"),
        "status_historico": [
            {
                "status": status_inicial,
                "etapa": etapa_inicial,
                "alterado_em": agora,
            }
        ],
        "cliente": {
            "nome": organization.get("name", ""),
            "cliente_id": organization.get("id", ""),
        },
        "capa_projeto": {
            "codigo": win.get("name", ""),
            "nome_vendedor": user.get("name"),
            "email_vendedor": user.get("email"),
        },
        "formacao_preco": {
            "valor": win.get("amount_total", 0),
        },
        "cronograma_execucao": {},
        "adicionais_projeto": {},
        "faturamento": {},
        "observacoes_gerais": [],
        "responsaveis": {},
    }


def _materializar_ganhos(wins):
    """Insere em warmup_projetos, com etapa 'Ganhos', os negócios ganhos que
    ainda não possuem documento correspondente (por negocio_id). Idempotente:
    negócios já materializados (em qualquer etapa, incluindo Arquivado ou
    etapas de warmup já iniciado) não são reprocessados."""
    ids = [w.get("id") for w in wins if w.get("id")]
    if not ids:
        return 0

    existentes = mongo.db.warmup_projetos.find(
        {"negocio_id": {"$in": ids}}, {"negocio_id": 1, "_id": 0}
    )
    ids_existentes = {doc["negocio_id"] for doc in existentes}

    novos = [w for w in wins if w.get("id") and w["id"] not in ids_existentes]
    for win in novos:
        mongo.db.warmup_projetos.insert_one(_documento_ganho(win))

    return len(novos)


def obter_novos_ganhos(days=30):
    """
    Sincroniza os negócios ganhos no RD Station (dentro da janela de `days`
    dias) como etapa "Ganhos" em warmup_projetos, e retorna os documentos
    atualmente na etapa "Ganhos".
    """
    # Obter o intervalo de datas
    start_date = DatetimeServices.data_anterior_ndias(days)
    end_date = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')  # Adiciona um dia ao end_date

    # Obter as negociações ganhas (wins) dentro da janela
    wins = RdServices().obter_negociacoes(win=True, closed_at_period="true", start_date=start_date, end_date=end_date) or []

    # Filtro defensivo: garante que apenas negócios efetivamente marcados como
    # ganhos no CRM entrem na fila, mesmo que o filtro da API do RD Station falhe.
    wins = [w for w in wins if w.get("win") is True]

    _materializar_ganhos(wins)

    return get_warmup_projetos_collection(etapa="Ganhos")


def deletar_negociacao(negociacao_id):
    """
    Deleta um registro da negociação através do ID.
    """
    try:
        resultado = mongo.db.negociacoes.delete_one({"_id": negociacao_id})
        if resultado.deleted_count == 1:
            return success_response("Negociação deletada com sucesso.")
        else:
            return error_response("Negociação não encontrada.")
    except Exception as e:
        return error_response(f"Erro ao deletar negociação: {e}")

def arquivar_negociacao(dados):
    """
    Arquiva um registro de Ganhos: atualiza o documento já existente em
    'warmup_projetos' (por negocio_id) para etapa "Arquivado", em vez de
    inserir um documento novo.
    """
    try:
        if not dados:
            return error_response("Nenhum dado enviado.")

        negocio_id = dados.get("negocio_id") or dados.get("id")
        if not negocio_id:
            return error_response("negocio_id é obrigatório.", 400)

        documento = mongo.db.warmup_projetos.find_one({"negocio_id": negocio_id})
        if not documento:
            return error_response("Registro de Ganhos não encontrado.", 404)

        modificados = atualizar_warmup_projeto(negocio_id, {
            "etapa": "Arquivado",
            "status": "Arquivado",
            "arquivado_em": datetime.utcnow(),
        })

        if not modificados:
            return error_response("Não foi possível arquivar o registro.", 500)

        return success_response("Negociação arquivada com sucesso.", {"negocio_id": negocio_id})

    except Exception as e:
        return error_response(f"Erro ao arquivar dados: {e}")

def iniciar_warmup(dados):
    """
    Avança um registro de Ganhos para Warmup Comercial: atualiza o documento
    já existente em 'warmup_projetos' (por negocio_id) definindo o
    responsável comercial, em vez de inserir um documento novo.
    """
    try:
        current_app.logger.debug(f"Payload recebido: {dados}")

        if not dados:
            return error_response("Nenhum dado enviado.", 400)

        # Verifica se o nome e o email do responsável foram enviados
        responsavel_nome = dados.get("responsavel", "")
        responsavel_email = dados.get("email_responsavel", "")

        if not responsavel_nome or not responsavel_email:
            return error_response("Nome e email do responsável comercial são obrigatórios.", 400)

        negocio_id = dados.get("negocio_id", "")
        documento = mongo.db.warmup_projetos.find_one({"negocio_id": negocio_id})
        if not documento:
            return error_response("Registro de Ganhos não encontrado.", 404)

        atualizacao = {
            "etapa": "Warmup Comercial",
            "status": "Aguardando",
            "inicio_warmup": datetime.utcnow(),
            "responsaveis": {
                "responsavel_comercial": {
                    "nome": responsavel_nome,
                    "email": responsavel_email,
                }
            },
        }

        current_app.logger.debug(f"Dados organizados para atualização: {atualizacao}")

        modificados = atualizar_warmup_projeto(negocio_id, atualizacao)

        current_app.logger.debug(f"Resultado da atualização: {modificados}")

        if not modificados:
            return error_response("Não foi possível atualizar o registro.", 500)

        return success_response("Registro avançado para Warmup Comercial.", {"negocio_id": negocio_id})

    except Exception as e:
        current_app.logger.error(f"Erro ao processar dados: {str(e)}")
        return error_response(f"Erro ao processar dados: {str(e)}", 500)
