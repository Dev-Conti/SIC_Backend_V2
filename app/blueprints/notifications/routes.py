import requests
from flask import request, render_template, current_app
from app.utils.decorators import require_auth
from app.utils.responses import success_response, error_response
from app.blueprints.m365.services import M365AppToken, M365Services
from . import notifications_bp
from .catalog import get_notification, missing_fields, resolve_recipient


@notifications_bp.route('/send', methods=['POST'])
@require_auth
def send_notification():
    payload = request.get_json(silent=True) or {}
    tipo = payload.get('tipo')
    contexto = payload.get('contexto') or {}

    if not tipo:
        return error_response("Campo 'tipo' é obrigatório.", 400)

    notification = get_notification(tipo)
    if not notification:
        return error_response(f"Tipo de notificação desconhecido: '{tipo}'.", 400)

    missing = missing_fields(notification, contexto)
    if missing:
        return error_response(
            f"Campos obrigatórios ausentes em 'contexto': {', '.join(missing)}.", 400
        )

    recipient_email = resolve_recipient(notification, contexto)
    subject = notification["subject"](contexto)
    body_content = render_template(
        notification["template"],
        base_url=current_app.config.get("FRONTEND_REDIRECT_URL"),
        **contexto,
    )

    try:
        access_token = M365AppToken().get_token()
        M365Services(access_token).send_mail(
            sender_email=notification["sender"],
            recipient_email=recipient_email,
            subject=subject,
            body_content=body_content,
        )
    except requests.RequestException as e:
        return error_response("Falha ao enviar notificação.", 500, str(e))

    return success_response("Notificação enviada com sucesso.", {"tipo": tipo})
