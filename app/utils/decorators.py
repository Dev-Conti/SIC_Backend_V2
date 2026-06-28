from functools import wraps
from flask import request, jsonify
from app.extensions import auth365  # Exemplo de extensão de autenticação usada
import jwt
from jwt import PyJWKClient, InvalidTokenError, DecodeError

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"message": "Unauthorized"}), 401

        try:
            # Remove o prefixo 'Bearer ' do token
            token = token.split()[1]

            # URL do JWKS da Microsoft
            jwks_url = f"{auth365.client.authority}/discovery/v2.0/keys"
            jwks_client = PyJWKClient(jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            # Decodifica o token e verifica o audience
            decoded_token = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=auth365.client.client_id  # Verifica se o token é para o backend
            )

            # Token válido
            return f(*args, **kwargs)

        except (InvalidTokenError, DecodeError, ValueError) as e:
            print(f"Erro ao verificar o token: {e}")
            return jsonify({"message": "Unauthorized"}), 401
        except Exception as e:
            print(f"Erro inesperado ao verificar o token: {e}")
            return jsonify({"message": "Internal Server Error"}), 500

    return decorated_function

def require_role(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('Authorization')
            user = auth365.decode_token(token)  # Decodifica o token e retorna as informações do usuário
            if not user or user.get('role') != required_role:
                return jsonify({"message": "Forbidden: insufficient permissions"}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

