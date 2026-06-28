from flask import Blueprint

# Criação da blueprint de autenticação
comercial_bp = Blueprint('comercial', __name__)

# Importa as rotas para registrá-las no blueprint
from . import routes
