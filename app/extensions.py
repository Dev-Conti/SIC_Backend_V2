from flask_pymongo import PyMongo
from pymongo import MongoClient
from msal import ConfidentialClientApplication
import jwt
from jwt import PyJWKClient
import redis
import pymssql
import os

class RedisClient:
    def __init__(self, app=None):
        self.client = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.client = redis.StrictRedis(
            host=app.config['REDIS_HOST'],
            port=app.config['REDIS_PORT'],
            password=app.config['REDIS_PASSWORD'],
            decode_responses=True
        )
class Auth365:
    """Classe para inicializar e gerenciar a autenticação com Microsoft 365 usando MSAL."""
    def __init__(self, app=None):
        self.client = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Inicializa o cliente MSAL com as configurações da aplicação."""
        self.client = ConfidentialClientApplication(
            client_id=app.config['MSAL_CLIENT_ID'],
            client_credential=app.config['MSAL_CLIENT_SECRET'],
            authority=app.config['MSAL_AUTHORITY']
        )
        self.scope = app.config['MSAL_SCOPE']
        self.redirect_uri = app.config['REDIRECT_URI']

    def verify_token(self, token):
        """Verifica a validade do token usando a chave pública da Microsoft."""
        try:
            # URL do JWKS da Microsoft para verificar a assinatura do token
            jwks_url = f"{self.client.authority}/discovery/v2.0/keys"
            jwks_client = PyJWKClient(jwks_url)

            # Extrai a chave correta para verificar a assinatura do token
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            # Decodifica e verifica o token usando a chave pública
            decoded_token = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.client.client_id
            )

            # Se não houver exceções, o token é válido
            return True
        except Exception as e:
            print(f"Erro ao verificar o token: {e}")
            return False
class DatabaseManager:
    def __init__(self, app=None):
        self.client = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Inicializa a conexão com o banco de dados Psoffice usando as configurações do arquivo de config."""
        db_config = app.config['DB_PSOFFICE_CONFIG']
        self.conn_str = {
            'server': db_config['server'],
            'database': db_config['database'],
            'user': db_config['username'],
            'password': db_config['password']
        }
        self.connection = None
        self.cursor = None

    def connect(self):
        """Estabelece a conexão com o banco de dados."""
        try:
            self.connection = pymssql.connect(**self.conn_str)
            self.cursor = self.connection.cursor()
        except pymssql.Error as e:
            raise ConnectionError(f"Erro ao conectar ao banco de dados: {e}")

    def execute_query(self, query):
        """Executa uma consulta no banco de dados e retorna os resultados."""
        if not self.connection or not self.cursor:
            raise Exception("Conexão não estabelecida. Chame o método 'connect' primeiro.")
        self.cursor.execute(query)
        return self.cursor.fetchall(), [desc[0] for desc in self.cursor.description]  # Resultados e cabeçalhos

    def close(self):
        """Fecha o cursor e a conexão."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
# Inicialização da extensão do MongoDB
mongo = PyMongo()
auth365 = Auth365()
redis_client = RedisClient()
db_psoffice = DatabaseManager()

