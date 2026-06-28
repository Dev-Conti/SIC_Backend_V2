from functools import wraps
from flask import request, jsonify
import jwt
import requests
from jwt.exceptions import InvalidTokenError
from app.config import Config
from app.extensions import redis_client
import logging

logger = logging.getLogger(__name__)

# URL para obter as chaves públicas do Azure AD
JWKS_URL = f"{Config.MSAL_AUTHORITY}/discovery/v2.0/keys"

# Token estático genérico
STATIC_TOKEN = Config.STATIC_TOKEN

def validate_tokens(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info("Iniciando validação dos tokens")

        jwt_token = request.headers.get('Authorization')
        if not jwt_token:
            logger.warning("Token JWT ausente")
            return jsonify({"error": "Token JWT ausente"}), 401

        try:
            logger.info("Validando token JWT")
            jwt_token = jwt_token.split(" ")[1]
            decoded_token = jwt.decode(jwt_token, Config.SECRET_KEY, algorithms=["HS256"])
            logger.info("Token JWT validado com sucesso")
        except InvalidTokenError as e:
            logger.error(f"Token JWT inválido: {e}")
            return jsonify({"error": "Token JWT inválido", "details": str(e)}), 401

        user_id = decoded_token.get('user_id')
        if not user_id:
            logger.warning("ID do usuário não encontrado no token JWT")
            return jsonify({"error": "ID do usuário não encontrado no token JWT"}), 401

        access_token = redis_client.client.get(f"{user_id}_access_token")
        if not access_token:
            logger.warning("Access token não encontrado no Redis")
            return jsonify({"error": "Access token não encontrado no Redis"}), 401

        request.access_token = access_token  # Armazena o token de acesso na requisição

        return f(*args, **kwargs)

    return decorated_function

def validate_static_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info("Iniciando validação do token estático")

        token = request.headers.get('Authorization')
        if not token:
            logger.warning("Token estático ausente")
            return jsonify({"error": "nao autorizado"}), 401

        token = token.split(" ")[1]
        if token != STATIC_TOKEN:
            logger.error("Token estático inválido")
            return jsonify({"error": "nao autorizado"}), 401

        logger.info("Token estático validado com sucesso")
        return f(*args, **kwargs)

    return decorated_function