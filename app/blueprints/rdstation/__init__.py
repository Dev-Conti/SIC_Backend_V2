from flask import Blueprint

# Criação da blueprint de autenticação
rdstation_bp = Blueprint('rdstation', __name__)

# Importa as rotas para registrá-las no blueprint
from . import routes
