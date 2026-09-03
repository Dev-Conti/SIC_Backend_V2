"""
Limpeza pontual dos registros indevidos criados pela versão revertida do
backfill de Ganhos (ver openspec/changes/ganhos-vira-etapa-warmup/design.md,
seção "Backfill do passivo pré-corte foi tentado e removido").

Remove:
  - todo documento em `warmup_projetos` com etapa == "Ganhos"
    (será re-sincronizado do zero, corretamente, na próxima chamada a
    GET /comercial/ganhos - nenhum outro etapa é afetado)
  - o marcador `system_flags._id == "ganhos_backfill_pre_corte"` (se existir)

Por padrão roda em modo "dry-run": só MOSTRA o que seria apagado, sem apagar
nada. Passe --confirm para executar de verdade.

Uso:
    python scripts/limpar_backfill_ganhos.py               # dry-run
    python scripts/limpar_backfill_ganhos.py --confirm      # apaga de verdade

A string de conexão vem de MONGO_URI (variável de ambiente, ou lida de um
arquivo .env na raiz de SIC_Backend_V2 caso a variável não esteja já
definida no ambiente - via python-dotenv se estiver instalado, ou por um
parser manual simples caso contrário, para não depender dessa lib estar
instalada em qualquer Python usado para rodar isto). Rode isso apontando
para o Mongo de PRODUÇÃO - ajuste MONGO_URI antes de rodar se o seu .env
local aponta para outro banco.
"""
import argparse
import os
import sys
from pathlib import Path


def _carregar_dotenv_manual(caminho_env):
    """Fallback sem depender de python-dotenv: parser simples de KEY=VALUE,
    só preenche variáveis que ainda não estão definidas no ambiente."""
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


_env_path = Path(__file__).resolve().parents[1] / ".env"
try:
    from dotenv import load_dotenv
    load_dotenv(_env_path)
except ImportError:
    _carregar_dotenv_manual(_env_path)

from pymongo import MongoClient  # noqa: E402


def conectar():
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("Erro: variável de ambiente MONGO_URI não definida.", file=sys.stderr)
        sys.exit(1)

    client = MongoClient(mongo_uri)
    try:
        db = client.get_default_database()
    except Exception:
        db_name = os.getenv("DEFAULT_DB")
        if not db_name:
            print(
                "Erro: MONGO_URI não tem um banco padrão na string de conexão, "
                "e DEFAULT_DB não está definido para usar como fallback.",
                file=sys.stderr,
            )
            sys.exit(1)
        db = client[db_name]
    return db


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Executa a exclusão de verdade. Sem essa flag, só mostra o que seria apagado (dry-run).",
    )
    args = parser.parse_args()

    db = conectar()

    ganhos = list(db.warmup_projetos.find(
        {"etapa": "Ganhos"},
        {"negocio_id": 1, "capa_projeto.codigo": 1, "name": 1, "ganho_em": 1, "rd_closed_at": 1},
    ))
    marcador = db.system_flags.find_one({"_id": "ganhos_backfill_pre_corte"})

    print(f"Banco: {db.name}")
    print(f"Documentos em warmup_projetos com etapa == 'Ganhos': {len(ganhos)}")
    for doc in ganhos[:20]:
        codigo = (doc.get("capa_projeto") or {}).get("codigo") or doc.get("name") or "(sem nome)"
        print(f"  - negocio_id={doc.get('negocio_id')!r} codigo={codigo!r} rd_closed_at={doc.get('rd_closed_at')!r}")
    if len(ganhos) > 20:
        print(f"  ... e mais {len(ganhos) - 20} documento(s)")

    print(f"Marcador system_flags._id == 'ganhos_backfill_pre_corte': {'existe' if marcador else 'não existe'}")

    if not args.confirm:
        print("\nDry-run: nada foi apagado. Rode novamente com --confirm para executar.")
        return

    resultado_ganhos = db.warmup_projetos.delete_many({"etapa": "Ganhos"})
    resultado_marcador = db.system_flags.delete_one({"_id": "ganhos_backfill_pre_corte"})

    print(f"\nApagados {resultado_ganhos.deleted_count} documento(s) em warmup_projetos (etapa 'Ganhos').")
    print(f"Marcador do backfill removido: {'sim' if resultado_marcador.deleted_count else 'não havia'}.")


if __name__ == "__main__":
    main()
