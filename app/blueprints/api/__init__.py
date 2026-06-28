from flask import Blueprint, jsonify
from app.utils.responses import success_response

# Criação da blueprint de autenticação
api_bp = Blueprint('api', __name__)

# Importa as rotas para registrá-las no blueprint
from .routes_psoffice import psoffice_bp
from .routes_rdstation import rdstation_bp

@api_bp.route('/', methods=['GET'])
def teste_api_route():
    """Endpoint principal que retorna uma mensagem indicando que o backend está conectado."""
    return success_response("Rota api v1 implantada com sucesso!", {"status": "online"})

# Registrar as sub-rotas
api_bp.register_blueprint(psoffice_bp, url_prefix='/psoffice')
api_bp.register_blueprint(rdstation_bp, url_prefix='/rdstation')
