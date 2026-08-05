from functools import wraps
from flask import request, jsonify
from app.config import Config
import jwt
from jwt import InvalidTokenError, DecodeError

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"message": "Unauthorized"}), 401

        try:
            # Remove o prefixo 'Bearer ' do token
            token = token.split()[1]

            # Decodifica o JWT emitido pelo próprio backend em /auth/callback
            # (HS256, assinado com JWT_SECRET_KEY — não é o token da Microsoft)
            decoded_token = jwt.decode(
                token,
                Config.JWT_SECRET_KEY,
                algorithms=["HS256"]
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

