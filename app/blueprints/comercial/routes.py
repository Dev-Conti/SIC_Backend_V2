from flask import jsonify, Blueprint, request
from flask_cors import cross_origin
from datetime import datetime
from app.utils.decorators import require_auth  # Use o nome correto da função
from app.utils.validators import validate_tokens  # Use o nome correto da função
from app.utils.responses import success_response, error_response
from . import comercial_bp
from .services import obter_novos_ganhos, atualizar_negociacoes, deletar_negociacao, arquivar_negociacao, iniciar_warmup

@comercial_bp.route('/', methods=['GET'])
def psoffice_users():
    """Endpoint principal que retorna uma mensagem indicando que o backend está conectado."""
    return jsonify({"message": "Rota comercial implantada com sucesso!", "status": "online"})

@comercial_bp.route('/ganhos', methods=['GET'])
def novas_negociacoes():
    """Endpoint que retorna as novas negociações."""
    # Obtém o parâmetro 'days' da query string, com valor padrão de 7
    days = request.args.get('days', default=7, type=int)
    
    # Chama a função com o parâmetro 'days'
    novas_negociacoes = obter_novos_ganhos(days=days)
    return jsonify(novas_negociacoes)

@comercial_bp.route('/atualizar-negociacoes', methods=['GET'])
def atualizar_negociacoes_route():
    """Endpoint que atualiza as negociações na coleção MongoDB."""
    response, status_code = atualizar_negociacoes()
    return jsonify({"status": "Negociações Atualizadas"})

@comercial_bp.route('/deletar-negociacao/<negociacao_id>', methods=['DELETE'])
@validate_tokens
def deletar_negociacao_route(negociacao_id):
    """Endpoint que deleta uma negociação na coleção MongoDB através do ID."""
    response, status_code = deletar_negociacao(negociacao_id)
    return jsonify(response), status_code

@comercial_bp.route('/arquivar', methods=['POST'])
@validate_tokens
def arquivar_dados():
    try:
        # Recebe os dados enviados no corpo da requisição (JSON)
        dados = request.get_json()

        response, status_code = arquivar_negociacao(dados)
        return jsonify(response), status_code

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@comercial_bp.route('/iniciar-warmup', methods=['POST'])
@validate_tokens
def iniciar_warmup_route():
    try:
        # Recebe os dados enviados no corpo da requisição (JSON)
        dados = request.get_json()

        response, status_code = iniciar_warmup(dados)
        return jsonify(response), status_code

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

