from flask import jsonify

def success_response(message, data=None):
    """Retorna uma resposta de sucesso padronizada."""
    return {
        "success": True,
        "message": message,
        "data": data
    }, 200

def error_response(message, status_code=400, error=None):
    """Retorna uma resposta de erro padronizada."""
    return {
        "success": False,
        "message": message,
        "error": error
    }, status_code
