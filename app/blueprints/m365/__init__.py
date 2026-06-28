from flask import Blueprint

# Criação da blueprint de autenticação
m365_bp = Blueprint('m365', __name__)

# Importa as rotas para registrá-las no blueprint
from . import routes
