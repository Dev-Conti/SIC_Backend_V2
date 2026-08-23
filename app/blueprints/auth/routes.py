from flask import Blueprint, redirect, url_for, request, session, jsonify
from app.extensions import auth365, redis_client
from app.config import Config
import jwt
import os
import requests
from datetime import datetime, timedelta

from . import auth_bp  # Importa o blueprint criado no __init__.py

def _extract_user_id_from_request():
    """Extrai o user_id do JWT interno enviado em Authorization, sem exigir
    que ele ainda esteja dentro da validade (`exp`).

    A fronteira real de confiança para /refresh e /logout não é o `exp` deste
    JWT, e sim a presença de um refresh_token válido no Redis para o user_id
    extraído — só a assinatura do JWT precisa ser íntegra (ver design.md da
    change add-jwt-refresh-flow).
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None, None

    try:
        token = auth_header.split()[1]
    except IndexError:
        return None, None

    try:
        payload = jwt.decode(
            token,
            Config.JWT_SECRET_KEY,
            algorithms=['HS256'],
            options={"verify_exp": False}
        )
    except jwt.InvalidTokenError:
        return None, None

    return payload.get('user_id'), payload.get('permissions', [])

@auth_bp.route('/login', methods=['GET'])
def login():
    """Rota para iniciar o fluxo de login com Microsoft 365."""
    auth_url = auth365.client.get_authorization_request_url(
        scopes=[auth365.scope],
        redirect_uri=auth365.redirect_uri
    )
    return redirect(auth_url)

@auth_bp.route('/callback', methods=['GET'])
def callback():
    """Rota de callback para lidar com a resposta do login da Microsoft."""
    code = request.args.get('code')
    token = request.args.get('token')

    if token:
        frontend_url = Config.FRONTEND_REDIRECT_URL
        url_redirect = f"{frontend_url}?token={token}"
        return redirect(url_redirect)

    if not code:
        return jsonify({"error": "Código de autorização não fornecido."}), 400

    try:
        # Passo 1: Obtém o token de acesso para o Microsoft Graph
        result_graph = auth365.client.acquire_token_by_authorization_code(
            code=code,
            scopes=["https://graph.microsoft.com/.default"],
            redirect_uri=auth365.redirect_uri
        )

        if 'access_token' in result_graph:
            access_token_graph = result_graph['access_token']
            refresh_token = result_graph['refresh_token']
            id_token = result_graph['id_token']

            # Passo 2: Armazena os tokens no Redis
            user_info = jwt.decode(id_token, options={"verify_signature": False})
            user_id = user_info['sub']

            redis_client.client.set(f"{user_id}_access_token", access_token_graph, ex=3600)  # Expira em 1 hora
            redis_client.client.set(f"{user_id}_refresh_token", refresh_token, ex=3600*24*30)  # Expira em 30 dias

            # Passo 3: Gera um JWT próprio para o frontend
            expiration = datetime.utcnow() + timedelta(hours=1)
            jwt_payload = {
                'user_id': str(user_id),
                'exp': expiration,
                'permissions': user_info.get('roles', [])
            }

            jwt_secret_key = Config.JWT_SECRET_KEY

            jwt_token = jwt.encode(jwt_payload, jwt_secret_key, algorithm='HS256')

            # Redireciona para o frontend com o JWT
            frontend_url = Config.REDIRECT_URI
            url_redirect = f"{frontend_url}?token={jwt_token}"
            return redirect(url_redirect)

        return jsonify({"error": "Falha ao adquirir os tokens.", "details": result_graph.get('error_description')}), 400

    except Exception as e:
        return jsonify({"error": str(e), "message": "Erro interno do servidor", "success": False}), 500

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Renova o JWT interno usando o refresh_token do Graph já armazenado no
    Redis, sem exigir um novo login interativo via Microsoft 365."""
    user_id, permissions = _extract_user_id_from_request()
    if not user_id:
        return jsonify({"error": "Token inválido."}), 401

    stored_refresh_token = redis_client.client.get(f"{user_id}_refresh_token")
    if not stored_refresh_token:
        return jsonify({"error": "Sessão expirada. Faça login novamente."}), 401

    result = auth365.client.acquire_token_by_refresh_token(
        stored_refresh_token,
        scopes=["https://graph.microsoft.com/.default"]
    )

    if 'access_token' not in result:
        # Refresh token revogado/expirado no Azure AD: só aqui exigimos login completo.
        return jsonify({"error": "Não foi possível renovar a sessão.", "details": result.get('error_description')}), 401

    new_access_token = result['access_token']
    # O Graph pode rotacionar o refresh_token a cada uso; sempre persistimos o mais recente.
    new_refresh_token = result.get('refresh_token', stored_refresh_token)

    redis_client.client.set(f"{user_id}_access_token", new_access_token, ex=3600)  # Expira em 1 hora
    redis_client.client.set(f"{user_id}_refresh_token", new_refresh_token, ex=3600 * 24 * 30)  # Expira em 30 dias

    expiration = datetime.utcnow() + timedelta(hours=1)
    new_jwt_payload = {
        'user_id': str(user_id),
        'exp': expiration,
        'permissions': permissions
    }
    new_jwt_token = jwt.encode(new_jwt_payload, Config.JWT_SECRET_KEY, algorithm='HS256')

    return jsonify({"token": new_jwt_token})

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Rota para logout do usuário.

    Usa o user_id extraído do JWT em Authorization — o `session.get('user_id')`
    anterior nunca era populado em nenhum lugar do fluxo de login, então a
    limpeza do Redis nunca acontecia de fato (achado ao implementar a change
    add-jwt-refresh-flow: sem isso, /auth/refresh continuaria renovando a
    sessão de um usuário mesmo após o "logout" no frontend).
    """
    user_id, _ = _extract_user_id_from_request()
    if user_id:
        redis_client.client.delete(f"{user_id}_access_token")
        redis_client.client.delete(f"{user_id}_refresh_token")
    session.clear()  # Limpa a sessão do usuário (não usada para autenticação via JWT, mantido por precaução)
    return jsonify({"message": "Logout bem-sucedido!"})

@auth_bp.route('/session', methods=['GET'])
def get_session():
    """Rota de teste para retornar o conteúdo da sessão."""
    return jsonify(dict(session))