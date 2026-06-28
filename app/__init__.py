import os
from flask import Flask, jsonify
from flask_cors import CORS
from .config import Config
from .extensions import mongo, auth365, redis_client, db_psoffice
from .blueprints.main import main_bp
from .blueprints.auth import auth_bp
from .blueprints.m365 import m365_bp
from .blueprints.psoffice import psoffice_bp
from .blueprints.warmup import warmup_bp
from .blueprints.rdstation import rdstation_bp
from .blueprints.comercial import comercial_bp
from .blueprints.users import users_bp
from .blueprints.reports import reports_bp
from .blueprints.suporte import suporte_bp
from .blueprints.deskmanager import deskmanager_bp
from .blueprints.api import api_bp
from dotenv import load_dotenv
load_dotenv(override=True)



def create_app():
    load_dotenv(override=True)


    app = Flask(__name__)
    app.config.from_object(Config)

    
    
    CORS(app, resources={
        r"/*": {
            "origins": [
                "http://localhost:3000",  # Para seu frontend rodando na porta 3001 (caso seja esse o caso)
                "https://sic.conticonsultoria.cloud"  # Para o frontend acessando pela URL oficial
            ],
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    # Inicializa extensões
    
    mongo.init_app(app)
    auth365.init_app(app)
    redis_client.init_app(app)
    db_psoffice.init_app(app)
    
    # Testa a conexão com o MongoDB
    try:
        mongo.cx.admin.command('ping')
        print("Conexão com o MongoDB bem-sucedida!")
    except Exception as e:
        print(f"Erro ao conectar ao MongoDB: {e}")

    # Registra blueprints
    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(users_bp, url_prefix='/users')    
    app.register_blueprint(m365_bp, url_prefix='/m365')
    app.register_blueprint(warmup_bp, url_prefix='/warmup')
    app.register_blueprint(psoffice_bp, url_prefix='/psoffice')
    app.register_blueprint(rdstation_bp, url_prefix='/rdstation')
    app.register_blueprint(deskmanager_bp, url_prefix='/deskmanager')
    app.register_blueprint(comercial_bp, url_prefix='/comercial')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(suporte_bp, url_prefix='/suporte')
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    


    # Adiciona manipulador global de erros
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Manipula exceções não tratadas e retorna uma resposta JSON."""
        response = {
            "success": False,
            "message": "Erro interno do servidor",
            "error": str(e)
        }
        return jsonify(response), 500

    return app

def test_mongo_connection():
    """Função para testar a conexão com o MongoDB."""
    try:
        # Verifica se consegue acessar o banco 'admin'
        mongo.cx.admin.command('ping')
        print("Conexão com o MongoDB bem-sucedida!")
    except Exception as e:
        print(f"Erro ao conectar ao MongoDB: {e}")

def test_redis_connection():
    """Função para testar a conexão com o Redis."""
    try:
        # Verifica se consegue acessar o Redis
        redis_client.client.ping()
        print("Conexão com o Redis bem-sucedida!")
    except Exception as e:
        print(f"Erro ao conectar ao Redis: {e}")

def test_db_psoffice_connection():
    """Função para testar a conexão com o banco de dados Psoffice."""
    try:
        db_psoffice.connect()
        print("Conexão com o banco de dados Psoffice bem-sucedida!")
        db_psoffice.close()
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados Psoffice: {e}")