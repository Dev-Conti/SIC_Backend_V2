SENDER = "warmup@conticonsultoria.com.br"
FIXED_RECIPIENT_FINANCEIRO = "junia.mendes@conticonsultoria.com.br"

NOTIFICATION_CATALOG = {
    "warmup_novo_comercial": {
        "sender": SENDER,
        "recipient_field": "responsavel_email",
        "subject": lambda ctx: f"Novo Warmup Disponível: {ctx['nome_projeto']}",
        "template": "emails/warmup_novo_comercial.html",
        "required_fields": ["responsavel_nome", "cliente", "nome_projeto", "id_negociacao"],
    },
    "projeto_encerramento_solicitado": {
        "sender": SENDER,
        "fixed_recipient": FIXED_RECIPIENT_FINANCEIRO,
        "subject": lambda ctx: f"Solicitação de Encerramento do Projeto {ctx['codigo']}",
        "template": "emails/projeto_encerramento_solicitado.html",
        "required_fields": ["codigo"],
    },
    "projeto_encerrado": {
        "sender": SENDER,
        "recipient_field": "gerente_email",
        "subject": lambda ctx: f"Projeto {ctx['codigo']} Encerrado com Sucesso",
        "template": "emails/projeto_encerrado.html",
        "required_fields": ["gerente_nome", "codigo"],
    },
    "warmup_atribuido_responsavel": {
        "sender": SENDER,
        "recipient_field": "socio_responsavel_email",
        "subject": lambda ctx: f"Você foi atribuído como Responsável do Projeto {ctx['codigo']}",
        "template": "emails/warmup_atribuido_responsavel.html",
        "required_fields": ["socio_responsavel_nome", "codigo"],
    },
    "warmup_novo_financeiro": {
        "sender": SENDER,
        "fixed_recipient": FIXED_RECIPIENT_FINANCEIRO,
        "subject": lambda ctx: "Novo Warmup disponível para análise do financeiro",
        "template": "emails/warmup_novo_financeiro.html",
        "required_fields": ["item_id"],
    },
    "warmup_correcao_pendente_financeiro": {
        "sender": SENDER,
        "recipient_field": "gerente_email",
        "subject": lambda ctx: "Formulário pendente de correção no Warmup Financeiro",
        "template": "emails/warmup_correcao_pendente_financeiro.html",
        "required_fields": [],
    },
    "warmup_correcao_pendente_comercial": {
        "sender": SENDER,
        "recipient_field": "responsavel_email",
        "subject": lambda ctx: "Formulário pendente de correção no Warmup Comercial",
        "template": "emails/warmup_correcao_pendente_comercial.html",
        "required_fields": [],
    },
    "warmup_atribuido_gerente": {
        "sender": SENDER,
        "recipient_field": "gerente_email",
        "subject": lambda ctx: f"Você foi atribuído como Gerente do Projeto {ctx['codigo']}",
        "template": "emails/warmup_atribuido_gerente.html",
        "required_fields": ["gerente_nome", "cliente_nome", "codigo", "item_id"],
    },
}


def get_notification(tipo):
    return NOTIFICATION_CATALOG.get(tipo)


def missing_fields(notification, contexto):
    """Fields required for template rendering, plus the recipient field when not fixed."""
    required = list(notification["required_fields"])
    if "fixed_recipient" not in notification:
        required.append(notification["recipient_field"])
    return [field for field in required if not contexto.get(field)]


def resolve_recipient(notification, contexto):
    if "fixed_recipient" in notification:
        return notification["fixed_recipient"]
    return contexto[notification["recipient_field"]]
