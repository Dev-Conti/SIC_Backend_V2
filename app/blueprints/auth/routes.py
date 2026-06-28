from flask import Blueprint, redirect, url_for, request, session, jsonify
from app.extensions import auth365, redis_client
from app.config import Config
import jwt
import os
import requests
from datetime import datetime, timedelta

from . import auth_bp  # Importa o blueprint criado no __init__.py

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

@auth_bp.route('/logout', methods=['GET'])
def logout():
    """Rota para logout do usuário."""
    user_id = session.get('user_id')
    if user_id:
        redis_client.client.delete(f"{user_id}_access_token")
        redis_client.client.delete(f"{user_id}_refresh_token")
    session.clear()  # Limpa a sessão do usuário
    return jsonify({"message": "Logout bem-sucedido!"})

@auth_bp.route('/session', methods=['GET'])
def get_session():
    """Rota de teste para retornar o conteúdo da sessão."""
    return jsonify(dict(session))