import logging
from flask import jsonify, request
from . import rdstation_bp
from .services import export_deals, export_deals_proposta_comercial, processar_webhook_deal_updated
from app.utils.validators import validate_tokens, validate_static_token, validate_static_token_query
from app.utils.responses import success_response, error_response
from .services import RdServices

logger = logging.getLogger(__name__)

@rdstation_bp.route('/', methods=['GET'])
def rd_test():
    """Endpoint principal que retorna uma mensagem indicando que o backend está conectado."""
    return success_response("Rota rdstation implantada com sucesso!", {"status": "online"})

@rdstation_bp.route('/deals', methods=['GET'])
@validate_tokens
def export_deals_route():
    """Endpoint que exporta os dados das negociações do CRM."""
    win = request.args.get('win')
    dados = export_deals(win=win)
    if dados is not None:
        return success_response("Negociações exportadas com sucesso!", dados)
    else:
        return error_response("Erro ao exportar negociações", 500)
    

@rdstation_bp.route('/deals-proposta-comercial', methods=['GET'])
@validate_tokens
def export_deals_in_proposta_route():
    """Endpoint que exporta os dados das negociações em aberto na etapa de 
    proposta comercial e do CRM."""

    dados = export_deals_proposta_comercial()
    if dados is not None:
        return success_response("Negociações exportadas com sucesso!", dados)
    else:
        return error_response("Erro ao exportar negociações", 500)
    
@rdstation_bp.route('/webhook/deal-updated', methods=['POST'])
@validate_static_token_query
def webhook_deal_updated_route():
    """Recebe o webhook `crm_deal_updated` do RD Station CRM e reconcilia os
    campos RD-owned do negócio correspondente em `warmup_projetos` (etapa
    "Ganhos"). Autenticado por token estático na query string (`?token=`).

    Responde 200 mesmo quando o evento é ignorado ou o processamento falha
    (o erro é logado): o RD Station só exige uma resposta 2xx. Um evento
    perdido é recuperado por `GET /comercial/ganhos`, que reconcilia os
    negócios de "Ganhos" com a listagem de ganhos da janela de `days` dias.
    """
    try:
        resultado = processar_webhook_deal_updated(request.get_json(silent=True))
    except Exception:
        logger.exception("Erro ao processar webhook crm_deal_updated do RD Station")
        resultado = "erro"

    return success_response("Evento processado.", {"resultado": resultado})


@rdstation_bp.route('/testes', methods=['GET'])
@validate_static_token
def testes_route():
    """Endpoint de testes"""

    dados = RdServices.obter_pipelines()
    if dados is not None:
        return success_response("dados exportadas com sucesso!", dados)
    else:
        return error_response("Erro ao exportar dados", 500)
