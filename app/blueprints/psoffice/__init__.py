from flask import Blueprint

# Criação da blueprint de autenticação
psoffice_bp = Blueprint('psoffice', __name__)

# Importa as rotas para registrá-las no blueprint
from . import routes
