from flask import jsonify, request
from . import suporte_bp
from ...utils.connection_tests import test_mongo_connection, test_redis_connection, test_db_psoffice_connection
from .services import ChamadosSuporte
from app.extensions import mongo

@suporte_bp.route('/', methods=['GET'])
def home():
    """Endpoint principal que retorna uma mensagem indicando que o backend está conectado."""
    return jsonify({
        "message": "Rota de Suporte implantada com sucesso!",
        "status": "online",
    })

@suporte_bp.route('/criar', methods=['POST'])
def criar_chamado():
    chamados_service = ChamadosSuporte(mongo)
    dados = request.json
    response = chamados_service.criar_chamado(dados)
    return jsonify(response)

@suporte_bp.route('/listar', methods=['GET'])
def listar_chamados():
    chamados_service = ChamadosSuporte(mongo)
    response = chamados_service.listar_chamados()
    return jsonify(response)

@suporte_bp.route('/listar/<chamado_id>', methods=['GET'])
def listar_chamado_unico(chamado_id):
    chamados_service = ChamadosSuporte(mongo)
    response = chamados_service.listar_chamado_unico(chamado_id)
    return jsonify(response)

@suporte_bp.route('/editar/<chamado_id>', methods=['PUT'])
def editar_chamado(chamado_id):
    chamados_service = ChamadosSuporte(mongo)
    dados = request.json
    response = chamados_service.editar_chamado(chamado_id, dados)
    return jsonify(response)

@suporte_bp.route('/deletar/<chamado_id>', methods=['DELETE'])
def deletar_chamado(chamado_id):
    chamados_service = ChamadosSuporte(mongo)
    response = chamados_service.deletar_chamado(chamado_id)
    return jsonify(response)

