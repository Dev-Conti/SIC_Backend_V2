from flask import Blueprint

# Criação da blueprint de autenticação
warmup_bp = Blueprint('warmup', __name__)

# Importa as rotas para registrá-las no blueprint
from . import routes
