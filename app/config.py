import os
import logging
from dotenv import load_dotenv

class Config:
    load_dotenv(dotenv_path='/root/sic-conti-v2/sic-backend/.env', override=True)
    # Configurações básicas
    # Padrão 'development' é proposital: só envia e-mail para destinatários
    # reais e reduz o nível de log quando FLASK_ENV é explicitamente 'production'.
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    LOG_LEVEL = logging.DEBUG if FLASK_ENV == 'development' else logging.INFO
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    FRONTEND_REDIRECT_URL = os.getenv('FRONTEND_REDIRECT_URL')
    FRONTEND_BASE_URL = os.getenv('FRONTEND_BASE_URL')
    
    # Configurações do MongoDB
    MONGO_URI = os.getenv('MONGO_URI')
    DEFAULT_DB = os.getenv('DEFAULT_DB')
    
    # Configurações do OAuth 2.0 (Microsoft 365)
    MSAL_CLIENT_ID = os.getenv('MSAL_CLIENT_ID')
    MSAL_CLIENT_SECRET = os.getenv('MSAL_CLIENT_SECRET')
    MSAL_AUTHORITY = os.getenv('MSAL_AUTHORITY')
    MSAL_SCOPE = os.getenv('MSAL_SCOPE')
    MSAL_TENANT_ID = os.getenv('MSAL_TENANT_ID')
    BASE_URL = os.getenv('REDIRECT_URI')
    REDIRECT_URI = os.getenv('REDIRECT_URI')
    
    # URL do Power Automate
    POWER_AUTOMATE_URL = os.getenv('POWER_AUTOMATE_URL')
    
    # Configurações do Redis
    REDIS_HOST = os.getenv('REDIS_HOST')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
    
    # Tokens de serviços externos
    TOKEN_PSOFFICE = os.getenv('TOKEN_PSOFFICE')
    TOKEN_RD = os.getenv('TOKEN_RD')
    DESK_PUBLIC_KEY= os.getenv('DESK_PUBLIC_KEY')
    DESK_OPERADOR_KEY= os.getenv('DESK_OPERADOR_KEY')
    DESK_API_URL = "https://api.desk.ms"
    PSOFFICE_API_URL = 'https://psofficeapp.com.br/conti'

    #Configuração do banco de dados Psoffice
    DB_PSOFFICE_CONFIG = {
        "server": os.getenv('DB_SERVER_PSOFFICE'),
        "database": os.getenv('DB_NAME_PSOFFICE'),
        "username": os.getenv('DB_USERNAME_PSOFFICE'),
        "password": os.getenv('DB_PASSWORD_PSOFFICE')
    }
    # Tamanho máximo do pool de conexões com o Psoffice (SQL Server)
    DB_PSOFFICE_POOL_SIZE = int(os.getenv('DB_PSOFFICE_POOL_SIZE', 5))

    # TTL (segundos) do cache Redis para leituras do Psoffice
    PSOFFICE_CACHE_TTL_SECONDS = int(os.getenv('PSOFFICE_CACHE_TTL_SECONDS', 600))

    STATIC_TOKEN = os.getenv('STATIC_TOKEN')



