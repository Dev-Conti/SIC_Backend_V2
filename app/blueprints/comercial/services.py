from app.extensions import mongo
import requests
import pandas as pd
import json
import os
from pymongo import MongoClient
from app.config import Config
from app.blueprints.rdstation.services import RdServices, export_deals
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

def obter_novos_ganhos(days=7):
    """
    Retorna todas as negociações cujo campo 'win' é True e que não estão presentes na coleção 'warmup_projetos'.
    """
    # Obter o intervalo de datas
    start_date = DatetimeServices.data_anterior_ndias(days)
    end_date = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')  # Adiciona um dia ao end_date

    # Obter todas as negociações ganhas (wins)
    wins = RdServices().obter_negociacoes(win=True, closed_at_period="true", start_date=start_date, end_date=end_date)

    # Filtro defensivo: garante que apenas negócios efetivamente marcados como
    # ganhos no CRM entrem na fila, mesmo que o filtro da API do RD Station falhe.
    wins = [w for w in wins if w.get("win") is True]

    # Extrair os IDs das negociações ganhas
    win_ids = [win["id"] for win in wins]

    # Buscar os IDs presentes na coleção 'warmup_projetos'
    warmup_ids = mongo.db.warmup_projetos.find(
        {"negocio_id": {"$in": win_ids}},
        {"negocio_id": 1, "_id": 0}
    )
    warmup_ids = {doc["negocio_id"] for doc in warmup_ids}

    # Filtrar os documentos que estão em 'wins' e não estão em 'warmup_projetos'
    novos_ganhos = [win for win in wins if win["id"] not in warmup_ids]

    return novos_ganhos


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
    Arquiva uma negociação na coleção 'warmup_projetos'.
    """
    try:
        if not dados:
            return error_response("Nenhum dado enviado.")

        # Organizando os dados no formato desejado
        dados_insert = {
            "negocio_id": dados.get("id", ""),
            "name": dados.get("name", ""),
            "etapa": "Arquivado",
            "status": "Arquivado",
            "arquivado_em": datetime.utcnow()
        }


        # Insere os dados na coleção
        resultado = mongo.db.warmup_projetos.insert_one(dados_insert)


        # Resposta com o ID do documento inserido
        return success_response("Dados inseridos com sucesso.", {"document_id": str(resultado.inserted_id)})

    except Exception as e:
        return error_response(f"Erro ao arquivar dados: {e}")

def iniciar_warmup(dados):
    """
    Processa os dados para iniciar o warmup comercial.
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

        # Organizando os dados no formato desejado
        dados_insert = {
            "negocio_id": dados.get("negocio_id", ""),
            "etapa": "Warmup Comercial",
            "status": "Aguardando",
            "inicio_warmup": datetime.utcnow(),
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

        current_app.logger.debug(f"Dados organizados para inserção: {dados_insert}")

        # Obtém a coleção onde os dados serão inseridos
        collection = mongo.db.warmup_projetos

        # Insere os dados na coleção
        resultado = collection.insert_one(dados_insert)

        current_app.logger.debug(f"Resultado da inserção: {resultado.inserted_id}")

        # Resposta com o ID do documento inserido
        return success_response("Dados inseridos com sucesso.", {"document_id": str(resultado.inserted_id)})

    except Exception as e:
        current_app.logger.error(f"Erro ao processar dados: {str(e)}")
        return error_response(f"Erro ao processar dados: {str(e)}", 500)
