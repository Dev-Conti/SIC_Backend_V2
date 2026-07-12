from flask import jsonify, request
from app.utils.validators import validate_tokens
from . import m365_bp
from app.blueprints.m365.services import M365Services,M365AppToken
from app.utils.responses import success_response, error_response
from app.extensions import redis_client
import jwt
import logging

logger = logging.getLogger(__name__)

@m365_bp.route('/', methods=['GET'])
def m365_users():
    """Endpoint principal que retorna uma mensagem indicando que o backend está conectado."""
    return jsonify({"message": "Rota m365 implantada com sucesso!", "status": "online"})

@m365_bp.route('/profile', methods=['GET'])
@validate_tokens
def get_profile():
    logger.debug("Iniciando a rota /profile")
    try:
        access_token = request.access_token  # Obtém o token de acesso da requisição
        m365_service = M365Services(access_token)
        user_profile = m365_service.get_complete_user_profile()

        return success_response("Perfil do usuário obtido com sucesso", user_profile)
    except Exception as e:
        return error_response("Erro ao obter o perfil do usuário", 500, str(e))

@m365_bp.route('/channel_members', methods=['GET'])
@validate_tokens
def get_channel_members():
    try:
        group_id = request.args.get('group_id')
        channel_id = request.args.get('channel_id')
        
        if not group_id or not channel_id:
            return error_response("Os parâmetros 'group_id' e 'channel_id' são obrigatórios", 400)
        
        app_token_service = M365AppToken()
        app_token = app_token_service.get_token()
        m365_service = M365Services(app_token)
        members = m365_service.get_channel_members(group_id, channel_id)

        return success_response("Membros do canal obtidos com sucesso", members)
    except Exception as e:
        return error_response("Erro ao obter os membros do canal", 500, str(e))

@m365_bp.route('/group_members', methods=['GET'])
@validate_tokens
def get_group_members():
    try:
        group_id = request.args.get('group_id')
        if not group_id:
            return error_response("O parâmetro 'group_id' é obrigatório", 400)
        app_token_service = M365AppToken()
        app_token = app_token_service.get_token()
        m365_service = M365Services(app_token)
        members = m365_service.get_group_members(group_id)
        return success_response("Membros do grupo obtidos com sucesso", members)
    except Exception as e:
        return error_response("Erro ao obter os membros do grupo", 500, str(e))

@m365_bp.route('/groups', methods=['GET'])
@validate_tokens
def get_groups():
    logger.debug("Iniciando a rota /groups")
    try:
        app_token_service = M365AppToken()
        app_token = app_token_service.get_token()
        m365_service = M365Services(app_token)
        groups = m365_service.get_all_groups()

        return success_response("Grupos obtidos com sucesso", groups)
    except Exception as e:
        return error_response("Erro ao obter os grupos", 500, str(e))

@m365_bp.route('/group_channels', methods=['GET'])
@validate_tokens
def get_group_channels():
    logger.debug("Iniciando a rota /group_channels")
    try:
        group_id = request.args.get('group_id')
        
        if not group_id:
            return error_response("O parâmetro 'group_id' é obrigatório", 400)
        
        app_token_service = M365AppToken()
        app_token = app_token_service.get_token()
        m365_service = M365Services(app_token)
        channels = m365_service.get_group_channels(group_id)

        return success_response("Canais do grupo obtidos com sucesso", channels)
    except Exception as e:
        return error_response("Erro ao obter os canais do grupo", 500, str(e))

@m365_bp.route('/testes', methods=['GET'])
def m365_testes():
    """Endpoint principal que retorna uma mensagem indicando que o backend está conectado."""
    return jsonify({"message": "Rota m365 implantada com sucesso!", "status": "online"})


@m365_bp.route('/app_token_example', methods=['GET'])
def app_token_example():
    logger.debug("Iniciando a rota /app_token_example")
    try:
        app_token_service = M365AppToken()
        app_token = app_token_service.get_token()
        
        m365_service = M365Services(app_token)
        groups = m365_service.get_all_groups()

        return success_response("Grupos obtidos com sucesso usando token de aplicativo", groups)
    except Exception as e:
        return error_response("Erro ao obter os grupos usando token de aplicativo", 500, str(e))