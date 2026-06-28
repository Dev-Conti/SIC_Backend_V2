from flask import Blueprint

# Criação da blueprint de autenticação
suporte_bp = Blueprint('suporte', __name__)

# Importa as rotas para registrá-las no blueprint
from . import routes
