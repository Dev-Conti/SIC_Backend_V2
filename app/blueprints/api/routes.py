from flask import jsonify
from app.utils.responses import success_response
from . import api_bp

@api_bp.route('/', methods=['GET'])
def teste_api_route():
    """Endpoint principal que retorna uma mensagem indicando que o backend está conectado."""
    return success_response("Rota api v1 implantada com sucesso!", {"status": "online"})



