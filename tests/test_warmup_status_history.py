"""
Testes de app.blueprints.warmup.services.atualizar_warmup: gravação do
histórico de status (status_historico), incluindo o motivo/observação de um
"Voltar Etapa" quando presente.

Carrega services.py diretamente por caminho de arquivo (sem passar pelos
pacotes app/app.blueprints/app.blueprints.warmup), com stubs mínimos para
suas dependências de topo (app.config, app.extensions, bson, requests), para
não depender de Flask/PyMongo/etc. instalados. Usa uma coleção Mongo falsa em
memória (sem Mongo real), com find_one e update_one suficientes para o uso
feito por atualizar_warmup.

Rodar com: python -m unittest discover -s tests
"""
import copy
import importlib.util
import sys
import types
import unittest
from pathlib import Path


def _carregar_services_com_stubs():
    """Registra stubs para as dependências de topo de services.py em
    sys.modules e carrega o módulo real diretamente do arquivo, sem passar
    pelos __init__.py de app/app.blueprints/app.blueprints.warmup."""
    app_config_stub = types.ModuleType("app.config")
    app_config_stub.Config = object

    fake_mongo = types.SimpleNamespace(db=None)
    app_extensions_stub = types.ModuleType("app.extensions")
    app_extensions_stub.mongo = fake_mongo

    bson_stub = types.ModuleType("bson")
    bson_stub.ObjectId = object

    requests_stub = types.ModuleType("requests")

    for nome, modulo in {
        "app.config": app_config_stub,
        "app.extensions": app_extensions_stub,
        "bson": bson_stub,
        "requests": requests_stub,
    }.items():
        sys.modules.setdefault(nome, modulo)

    services_path = (
        Path(__file__).resolve().parents[1]
        / "app" / "blueprints" / "warmup" / "services.py"
    )
    spec = importlib.util.spec_from_file_location(
        "warmup_services_under_test", services_path
    )
    services = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(services)
    return services, fake_mongo


services, fake_mongo = _carregar_services_com_stubs()


class FakeUpdateResult:
    def __init__(self, modified_count):
        self.modified_count = modified_count


class FakeWarmupProjetosCollection:
    """Coleção falsa em memória com o mínimo usado por atualizar_warmup."""

    def __init__(self, documento_inicial):
        self._doc = copy.deepcopy(documento_inicial)

    def find_one(self, query):
        return copy.deepcopy(self._doc) if self._doc.get("negocio_id") == query.get("negocio_id") else None

    def update_one(self, query, update):
        if self._doc.get("negocio_id") != query.get("negocio_id"):
            return FakeUpdateResult(0)

        set_fields = update.get("$set", {})
        self._doc.update(set_fields)

        push = update.get("$push")
        if push:
            for campo, valor in push.items():
                self._doc.setdefault(campo, []).append(valor)

        return FakeUpdateResult(1)


class TestAtualizarWarmupStatusHistorico(unittest.TestCase):
    def setUp(self):
        self.documento = {
            "negocio_id": "NEG-1",
            "status": "Aguardando",
            "etapa": "Warmup Financeiro",
            "status_historico": [
                {"status": "Aguardando", "etapa": "Warmup Financeiro", "alterado_em": "2026-08-01T00:00:00"}
            ],
        }
        self.fake_collection = FakeWarmupProjetosCollection(self.documento)
        fake_mongo.db = types.SimpleNamespace(warmup_projetos=self.fake_collection)

    def test_voltar_etapa_com_observacao_grava_motivo_no_historico(self):
        modificados = services.atualizar_warmup(
            "NEG-1",
            {
                "etapa": "Warmup Comercial",
                "status": "Revisar",
                "observacao": "Faltou anexar a ficha cadastral assinada",
                "usuario": "Maria Souza",
            },
        )

        self.assertEqual(modificados, 1)
        historico = self.fake_collection._doc["status_historico"]
        self.assertEqual(len(historico), 2)
        nova_entrada = historico[-1]
        self.assertEqual(nova_entrada["status"], "Revisar")
        self.assertEqual(nova_entrada["etapa"], "Warmup Comercial")
        self.assertEqual(nova_entrada["observacao"], "Faltou anexar a ficha cadastral assinada")
        self.assertEqual(nova_entrada["usuario"], "Maria Souza")

    def test_avancar_etapa_sem_observacao_nao_grava_motivo(self):
        services.atualizar_warmup(
            "NEG-1",
            {"etapa": "Projeto Liberado", "status": "Liberado"},
        )

        historico = self.fake_collection._doc["status_historico"]
        nova_entrada = historico[-1]
        self.assertEqual(nova_entrada["status"], "Liberado")
        self.assertNotIn("observacao", nova_entrada)
        self.assertNotIn("usuario", nova_entrada)


if __name__ == "__main__":
    unittest.main()
