from flask import Blueprint

# Criação do blueprint de autenticação
auth_bp = Blueprint('auth', __name__)

# Importa as rotas para registrá-las no blueprint
from . import routes
