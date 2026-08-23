from flask_pymongo import PyMongo
from pymongo import MongoClient
from msal import ConfidentialClientApplication
import jwt
from jwt import PyJWKClient
import redis
import pymssql
import os
import queue
import threading
from contextlib import contextmanager

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
    """Pool de conexões com o SQL Server do Psoffice.

    Em vez de abrir/fechar uma conexão nova a cada query (custo de handshake
    + autenticação por requisição), mantém até `pool_size` conexões vivas e
    as reutiliza. Conexões são validadas antes do reuso (podem ter sido
    encerradas pelo SQL Server por inatividade) e sempre devolvidas ao pool
    em `finally`, mesmo se a query lançar exceção.
    """

    def __init__(self, app=None):
        self.conn_str = None
        self.pool_size = 5
        self._pool = None
        self._lock = threading.Lock()
        self._created = 0
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Configura o pool com as credenciais do Psoffice do config da app."""
        db_config = app.config['DB_PSOFFICE_CONFIG']
        self.conn_str = {
            'server': db_config['server'],
            'database': db_config['database'],
            'user': db_config['username'],
            'password': db_config['password']
        }
        self.pool_size = app.config.get('DB_PSOFFICE_POOL_SIZE', 5)
        self._pool = queue.Queue(maxsize=self.pool_size)
        self._created = 0

    def _create_connection(self):
        try:
            return pymssql.connect(**self.conn_str)
        except pymssql.Error as e:
            raise ConnectionError(f"Erro ao conectar ao banco de dados: {e}")

    def _is_alive(self, connection):
        """Confirma que uma conexão ociosa do pool ainda responde antes de reusá-la."""
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchall()
            cursor.close()
            return True
        except Exception:
            return False

    def _acquire(self):
        while True:
            try:
                connection = self._pool.get_nowait()
            except queue.Empty:
                with self._lock:
                    if self._created < self.pool_size:
                        self._created += 1
                        return self._create_connection()
                # Pool no limite: espera alguém devolver uma conexão.
                connection = self._pool.get()

            if self._is_alive(connection):
                return connection

            # Conexão morta (ex.: encerrada por inatividade) — descarta e cria outra.
            try:
                connection.close()
            except Exception:
                pass
            with self._lock:
                self._created -= 1
                self._created += 1
            return self._create_connection()

    def _release(self, connection):
        try:
            self._pool.put_nowait(connection)
        except queue.Full:
            # Não deveria acontecer (put sempre corresponde a um get anterior),
            # mas por segurança fecha em vez de vazar.
            try:
                connection.close()
            except Exception:
                pass
            with self._lock:
                self._created -= 1

    @contextmanager
    def get_connection(self):
        """Empresta uma conexão do pool e garante devolução mesmo em erro.

        Uso: `with db_psoffice.get_connection() as conn: ...`
        """
        connection = self._acquire()
        try:
            yield connection
        finally:
            self._release(connection)

    def execute_query(self, query):
        """Executa uma consulta usando uma conexão do pool e retorna (resultados, headers)."""
        with self.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query)
                return cursor.fetchall(), [desc[0] for desc in cursor.description]
            finally:
                cursor.close()

    def test_connection(self):
        """Verifica conectividade emprestando e devolvendo uma conexão do pool."""
        with self.get_connection():
            pass
# Inicialização da extensão do MongoDB
mongo = PyMongo()
auth365 = Auth365()
redis_client = RedisClient()
db_psoffice = DatabaseManager()

