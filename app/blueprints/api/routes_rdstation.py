from flask import Blueprint, request, jsonify
from app.utils.validators import validate_static_token
from app.utils.responses import success_response, error_response
from app.blueprints.rdstation.services import RdServices
from datetime import datetime

rdstation_bp = Blueprint('rdstation', __name__)


@rdstation_bp.route('/', methods=['GET'])
def teste_api_route():
    """Endpoint principal que retorna uma mensagem indicando que o backend está conectado."""
    return success_response("Rota api/rdstation implantada com sucesso!", {"status": "online"})

@rdstation_bp.route('/pipelines', methods=['GET'])
@validate_static_token
def pipelines_route():
    """Endpoint de testes"""

    dados = RdServices.obter_pipelines()
    if dados is not None:
        return success_response("dados exportadas com sucesso!", dados)
    else:
        return error_response("Erro ao exportar dados", 500)

@rdstation_bp.route('/empresas', methods=['GET'])
@validate_static_token
def empresas_route():
    """Endpoint de testes"""
    rd_services = RdServices()
    dados = rd_services.obter_empresas()
    
    if dados is not None:
        return success_response("dados exportadas com sucesso!", dados)
    else:
        return error_response("Erro ao exportar dados", 500)

@rdstation_bp.route('/negociacoes', methods=['GET'])
@validate_static_token
def negociacoes_route():
    """Endpoint de testes"""

    dados = RdServices.obter_negociacoes()
    if dados is not None:
        return success_response("dados exportadas com sucesso!", dados)
    else:
        return error_response("Erro ao exportar dados", 500)


@rdstation_bp.route('/testes', methods=['GET'])
@validate_static_token
def testes_route():
    """Endpoint de testes"""

    dados = RdServices.obter_pipelines()
    if dados is not None:
        return success_response("dados exportadas com sucesso!", dados)
    else:
        return error_response("Erro ao exportar dados", 500)
