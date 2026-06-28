from flask import Blueprint

# Criação da blueprint de autenticação
users_bp = Blueprint('users', __name__)

# Importa as rotas para registrá-las no blueprint
from . import routes
