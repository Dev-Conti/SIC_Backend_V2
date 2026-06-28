from flask import Blueprint

# Criação da blueprint de autenticação
main_bp = Blueprint('main', __name__)

# Importa as rotas para registrá-las no blueprint
from . import routes
