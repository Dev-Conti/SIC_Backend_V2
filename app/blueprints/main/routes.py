from flask import jsonify
from . import main_bp
from ...utils.connection_tests import test_mongo_connection, test_redis_connection, test_db_psoffice_connection

@main_bp.route('/', methods=['GET'])
def home():
    """Endpoint principal que retorna uma mensagem indicando que o backend está conectado."""
    
    return jsonify({
        "message": "Backend conectado com sucesso!",
        "status": "online"
        })

@main_bp.route('/favicon.ico')
def favicon():
    return '', 204  # Responde com um status 204 (sem conteúdo)

