from flask import jsonify, request
from app.utils.decorators import require_auth  # Use o nome correto da função
from app.utils.responses import success_response, error_response
from app.utils.validators import validate_tokens
from .services import PsofficeServices
from datetime import datetime
import logging
from . import psoffice_bp

psoffice_services = PsofficeServices()

@psoffice_bp.route('/', methods=['GET'])
@validate_tokens
def psoffice_users():
    """Endpoint principal que retorna uma mensagem indicando que o backend está conectado."""
    return success_response("Rota psoffice implantada com sucesso!", {"status": "online"})

@psoffice_bp.route('/centrosresultado', methods=['GET'])
@validate_tokens
def get_centros_resultado():
    """Endpoint para obter centros de resultado."""
    try:
        data = psoffice_services.get_centros_resultado()
        return success_response("Centros de resultado obtidos com sucesso.", data)
    except Exception as e:
        return error_response("Erro ao obter centros de resultado.", error=str(e))

@psoffice_bp.route('/pessoasjuridicas', methods=['GET'])
@validate_tokens
def buscar_pessoas_juridicas():
    """Endpoint para obter pessoas jurídicas."""
    try:
        data = psoffice_services.get_pessoas_juridicas()
        return success_response("Pessoas jurídicas obtidas com sucesso.", data)
    except Exception as e:
        return error_response("Erro ao obter pessoas jurídicas.", error=str(e))

@psoffice_bp.route('/projetos', methods=['GET'])
@validate_tokens
def buscar_projeto():
    """Endpoint para obter projeto."""
    try:
        ams = request.args.get('ams', 'false').lower() == 'true'
        if ams:
            data = psoffice_services.get_projetos_ams()
        else:
            data = psoffice_services.get_projetos()
        return success_response("Projetos obtidos com sucesso.", data)
    except Exception as e:
        return error_response("Erro ao obter projetos.", error=str(e))
    
@psoffice_bp.route('/testes', methods=['GET'])
def buscar_ausencias_psoffice():
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    cpf = request.args.get('cpf')
    
    if not data_inicio or not data_fim:
        return jsonify({"error": "Os parâmetros 'data_inicio' e 'data_fim' são obrigatórios."}), 400
    
    try:
        # Garantir que as datas estejam no formato yyyy-mm-dd
        data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').strftime('%Y-%m-%d')
        data_fim = datetime.strptime(data_fim, '%Y-%m-%d').strftime('%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Formato de data inválido. Use o formato yyyy-mm-dd."}), 400

    service = PsofficeServices()
    try:
        # Usar a nova função get_apontamentos_v2
        apontamentos = service.get_apontamentos_v2(data_inicio, data_fim)
        return jsonify(apontamentos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500



