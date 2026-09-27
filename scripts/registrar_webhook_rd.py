"""
Registra na conta do RD Station CRM o webhook `crm_deal_updated`, que chama
POST /rdstation/webhook/deal-updated neste backend sempre que um negócio é
alterado no RD (ver openspec/changes/rd-station-reconciliar-alteracoes).

Por padrão roda em modo "dry-run": lista os webhooks já cadastrados na conta
e MOSTRA o que seria cadastrado, sem criar nada. Passe --confirm para criar.
É idempotente: se já existir um webhook `crm_deal_updated` apontando para
este endpoint, nada é criado.

Uso:
    python scripts/registrar_webhook_rd.py --url-base https://SEU-BACKEND         # dry-run
    python scripts/registrar_webhook_rd.py --url-base https://SEU-BACKEND --confirm

Pré-requisitos:
  - O backend com o endpoint /rdstation/webhook/deal-updated já DEPLOYADO em
    --url-base (HTTPS obrigatório - exigência do RD Station). Registrar antes
    do deploy faz o RD enviar eventos para um endpoint inexistente.
  - TOKEN_RD: token de API da conta do RD Station (variável de ambiente ou
    .env na raiz de SIC_Backend_V2).
  - STATIC_TOKEN: DEVE ser o mesmo valor configurado no .env do servidor de
    PRODUÇÃO - é ele que o endpoint exige na query string (?token=). O do seu
    .env local pode ser diferente; se for, rode com o valor de produção:
        STATIC_TOKEN=<valor-de-producao> python scripts/registrar_webhook_rd.py ...
    (por variável de ambiente, não por argumento, para não ir ao histórico
    do shell).

O token vai na URL cadastrada porque o cadastro de webhook do RD só aceita
{event_type, http_method, url} - não há campo para header/secret. Por isso
ele pode aparecer em logs de acesso do servidor; use um STATIC_TOKEN dedicado
e longo, e rotacione-o (recadastrando o webhook) se houver suspeita de vazamento.
"""
import argparse
import os
import sys
from pathlib import Path
from urllib.parse import quote

import requests

API_WEBHOOKS = "https://crm.rdstation.com/api/v1/webhooks"
EVENT_TYPE = "crm_deal_updated"
CALLBACK_PATH = "/rdstation/webhook/deal-updated"


def _carregar_dotenv_manual(caminho_env):
    """Parser simples de KEY=VALUE; só preenche variáveis ainda não definidas
    no ambiente (assim uma variável exportada no shell tem precedência)."""
    if not caminho_env.exists():
        return
    for linha in caminho_env.read_text(encoding="utf-8", errors="replace").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        chave = chave.strip()
        valor = valor.strip().strip('"').strip("'")
        if chave and chave not in os.environ:
            os.environ[chave] = valor


_carregar_dotenv_manual(Path(__file__).resolve().parents[1] / ".env")


def _mascarar(texto, *segredos):
    for segredo in segredos:
        if segredo:
            texto = texto.replace(segredo, "***")
    return texto


def _listar_webhooks(token_rd):
    resposta = requests.get(API_WEBHOOKS, params={"token": token_rd}, headers={"accept": "application/json"}, timeout=20)
    if resposta.status_code != 200:
        raise SystemExit(f"Falha ao listar webhooks ({resposta.status_code}): {resposta.text[:300]}")
    dados = resposta.json()
    return dados if isinstance(dados, list) else dados.get("webhooks", [])


def main():
    parser = argparse.ArgumentParser(description="Registra o webhook crm_deal_updated do RD Station.")
    parser.add_argument("--url-base", required=True,
                        help="URL pública do backend em produção, ex.: https://api.exemplo.com (sem barra final)")
    parser.add_argument("--confirm", action="store_true", help="Cria o webhook de verdade (sem isso é só dry-run)")
    args = parser.parse_args()

    token_rd = os.getenv("TOKEN_RD")
    static_token = os.getenv("STATIC_TOKEN")
    if not token_rd:
        raise SystemExit("TOKEN_RD nao encontrado (variavel de ambiente ou .env).")
    if not static_token:
        raise SystemExit("STATIC_TOKEN nao encontrado (variavel de ambiente ou .env).")

    url_base = args.url_base.rstrip("/")
    if not url_base.startswith("https://"):
        raise SystemExit("--url-base precisa comecar com https:// (o RD Station exige HTTPS no webhook).")

    callback = f"{url_base}{CALLBACK_PATH}?token={quote(static_token, safe='')}"
    corpo = {"event_type": EVENT_TYPE, "http_method": "POST", "url": callback}

    print(f"Modo: {'CONFIRM (vai criar)' if args.confirm else 'dry-run (nao cria nada)'}")
    print("\nWebhooks ja cadastrados na conta do RD Station:")
    existentes = _listar_webhooks(token_rd)
    if not existentes:
        print("  (nenhum)")
    for w in existentes:
        print(f"  - uuid={w.get('uuid')} event_type={w.get('event_type')} status={w.get('status')} "
              f"url={_mascarar(str(w.get('url')), static_token)}")

    ja_existe = [w for w in existentes
                 if w.get("event_type") == EVENT_TYPE and CALLBACK_PATH in str(w.get("url", ""))]
    if ja_existe:
        print(f"\nJa existe um webhook {EVENT_TYPE} apontando para {CALLBACK_PATH} - nada a criar.")
        print("Se o token/URL mudou, atualize-o (PUT /webhooks/{uuid}) ou remova-o e rode de novo.")
        return 0

    print("\nSeria criado:")
    print(f"  POST {API_WEBHOOKS}?token=***")
    print(f"  {_mascarar(str(corpo), static_token)}")

    if not args.confirm:
        print("\n(dry-run) Nada foi criado. Rode com --confirm depois de confirmar que o backend "
              "esta deployado nessa URL.")
        return 0

    resposta = requests.post(API_WEBHOOKS, params={"token": token_rd}, json=corpo,
                             headers={"accept": "application/json"}, timeout=20)
    print(f"\nResposta do RD Station: HTTP {resposta.status_code}")
    print(_mascarar(resposta.text[:500], static_token))
    return 0 if resposta.status_code in (200, 201) else 1


if __name__ == "__main__":
    sys.exit(main())
