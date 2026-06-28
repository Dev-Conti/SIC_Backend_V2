from flask import Blueprint

# Criação da blueprint de autenticação
deskmanager_bp = Blueprint('deskmanager', __name__)

# Importa as rotas para registrá-las no blueprint
from . import routes
