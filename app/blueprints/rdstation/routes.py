from flask import jsonify, request
from . import rdstation_bp
from .services import export_deals, export_deals_proposta_comercial
from app.utils.validators import validate_tokens, validate_static_token
from app.utils.responses import success_response, error_response
from .services import RdServices

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
    
@rdstation_bp.route('/testes', methods=['GET'])
@validate_static_token
def testes_route():
    """Endpoint de testes"""

    dados = RdServices.obter_pipelines()
    if dados is not None:
        return success_response("dados exportadas com sucesso!", dados)
    else:
        return error_response("Erro ao exportar dados", 500)
