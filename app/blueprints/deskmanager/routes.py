from flask import jsonify
from app.utils.decorators import require_auth  # Use o nome correto da função
from app.utils.responses import success_response, error_response
from app.utils.validators import validate_tokens  # Use o nome correto da função
from . import deskmanager_bp
from .services import DeskManagerServices

desk_manager_services = DeskManagerServices()

@deskmanager_bp.route('/', methods=['GET'])
def psoffice_users():
    """Endpoint principal que retorna uma mensagem indicando que o backend está conectado."""
    return jsonify({"message": "Rota deskmanager implantada com sucesso!", "status": "online"})

@deskmanager_bp.route('/clientes', methods=['GET'])
@validate_tokens
def get_clientes():
    try:
        data = desk_manager_services.obter_clientes()
        return success_response("Clientes obtidos com sucesso", data)
    except Exception as e:
        return error_response("Erro ao obter clientes", error=str(e))

@deskmanager_bp.route('/contratos', methods=['GET'])
@validate_tokens
def get_contratos():
    try:
        data = desk_manager_services.obter_contratos()
        return success_response("Contratos obtidos com sucesso", data)
    except Exception as e:
        return error_response("Erro ao obter contratos", error=str(e))

@deskmanager_bp.route('/chamados-suporte', methods=['GET'])
@validate_tokens
def get_chamados_suporte():
    try:
        data = desk_manager_services.obter_chamados_suporte()
        return success_response("Chamados de suporte obtidos com sucesso", data)
    except Exception as e:
        return error_response("Erro ao obter chamados de suporte", error=str(e))

@deskmanager_bp.route('/usuarios', methods=['GET'])
@validate_tokens
def get_usuarios():
    try:
        data = desk_manager_services.obter_usuarios()
        return success_response("Usuários obtidos com sucesso", data)
    except Exception as e:
        return error_response("Erro ao obter usuários", error=str(e))

@deskmanager_bp.route('/chamado-historicos', methods=['GET'])
@validate_tokens
def get_chamado_historicos():
    try:
        data = desk_manager_services.obter_chamado_historicos()
        return success_response("Históricos de chamados obtidos com sucesso", data)
    except Exception as e:
        return error_response("Erro ao obter históricos de chamados", error=str(e))

@deskmanager_bp.route('/pesquisa-satisfacao', methods=['GET'])
@validate_tokens
def get_pesquisa_satisfacao():
    try:
        data = desk_manager_services.obter_pesquisa_satisfacao()
        return success_response("Pesquisas de satisfação obtidas com sucesso", data)
    except Exception as e:
        return error_response("Erro ao obter pesquisas de satisfação", error=str(e))

@deskmanager_bp.route('/testes', methods=['GET'])
@validate_tokens
def deskmanager_testes():

    data = desk_manager_services.obter_contratos()
    return jsonify(data)

