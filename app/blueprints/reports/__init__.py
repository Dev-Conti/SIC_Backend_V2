from flask import Blueprint

# Criação do blueprint para relatórios
reports_bp = Blueprint('reports', __name__)

# Importa as rotas para registrá-las no blueprint
from . import routes
