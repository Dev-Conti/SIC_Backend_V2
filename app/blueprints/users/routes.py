from flask import jsonify
from . import users_bp

@users_bp.route('/', methods=['GET'])
def home_users():
    """Endpoint principal que retorna uma mensagem indicando que o backend está conectado."""
    return jsonify({"message": "Rota Users implantada com sucesso!", "status": "online"})
