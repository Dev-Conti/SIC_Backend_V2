"""
Testes de app.blueprints.rdstation.services.reconciliar_campos_rd, cobrindo
a tarefa 1.1 de
openspec/changes/rd-station-reconciliar-alteracoes/tasks.md.

Carrega rdstation/services.py diretamente por caminho de arquivo, com stubs
mínimos para app.extensions/app.config - reconciliar_campos_rd é uma função
pura (sem I/O), então não precisamos de mongo/config reais para testá-la, só
que os dois módulos importados no topo do arquivo resolvam sem erro.

Rodar com: python -m unittest discover -s tests
"""
import importlib.util
import sys
import types
import unittest
from pathlib import Path


def _carregar_rdstation_services():
    app_config_stub = types.ModuleType("app.config")
    app_config_stub.Config = object

    app_extensions_stub = types.ModuleType("app.extensions")
    app_extensions_stub.mongo = types.SimpleNamespace(db=None)

    sys.modules["app.config"] = app_config_stub
    sys.modules["app.extensions"] = app_extensions_stub

    backend_root = Path(__file__).resolve().parents[1] / "app"
    spec = importlib.util.spec_from_file_location(
        "app.blueprints.rdstation.services", backend_root / "blueprints" / "rdstation" / "services.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestReconciliarCamposRd(unittest.TestCase):
    def setUp(self):
        self.services = _carregar_rdstation_services()

    def _deal(self, **overrides):
        base = {
            "id": "NEG-1",
            "name": "Projeto Atualizado",
            "amount_total": 5000,
            "closed_at": "2026-09-18T13:55:06.542-03:00",
            "organization": {"id": "org-1", "name": "Cliente Atualizado"},
            "user": {"name": "Vendedor Atualizado", "email": "vendedor@conticonsultoria.com.br"},
        }
        base.update(overrides)
        return base

    def _documento(self, **overrides):
        base = {
            "negocio_id": "NEG-1",
            "etapa": "Ganhos",
            "capa_projeto": {
                "codigo": "Projeto Antigo",
                "nome_vendedor": "Vendedor Antigo",
                "email_vendedor": "antigo@conticonsultoria.com.br",
                # Campo SIC-owned no mesmo sub-objeto - nunca deve aparecer
                # no resultado da reconciliação.
                "gerente_projeto": {"nome": "Gerente X", "email": "gerente@conticonsultoria.com.br"},
            },
            "cliente": {"nome": "Cliente Antigo", "cliente_id": "org-antigo"},
            "formacao_preco": {"valor": 1000},
            "rd_closed_at": "2026-09-01T00:00:00.000-03:00",
        }
        base.update(overrides)
        return base

    def test_campo_divergente_e_detectado(self):
        resultado = self.services.reconciliar_campos_rd(self._documento(), self._deal())

        self.assertIsNotNone(resultado)
        self.assertEqual(resultado["capa_projeto.codigo"], "Projeto Atualizado")
        self.assertEqual(resultado["capa_projeto.nome_vendedor"], "Vendedor Atualizado")
        self.assertEqual(resultado["capa_projeto.email_vendedor"], "vendedor@conticonsultoria.com.br")
        self.assertEqual(resultado["cliente.nome"], "Cliente Atualizado")
        self.assertEqual(resultado["cliente.cliente_id"], "org-1")
        self.assertEqual(resultado["formacao_preco.valor"], 5000)
        self.assertEqual(resultado["rd_closed_at"], "2026-09-18T13:55:06.542-03:00")

    def test_nenhum_campo_fora_da_allowlist_e_incluido(self):
        resultado = self.services.reconciliar_campos_rd(self._documento(), self._deal())

        allowlist = {
            "capa_projeto.codigo", "capa_projeto.nome_vendedor", "capa_projeto.email_vendedor",
            "cliente.nome", "cliente.cliente_id", "formacao_preco.valor", "rd_closed_at",
        }
        self.assertTrue(set(resultado.keys()).issubset(allowlist))
        self.assertNotIn("capa_projeto.gerente_projeto", resultado)
        self.assertNotIn("etapa", resultado)
        self.assertNotIn("negocio_id", resultado)

    def test_nenhuma_diferenca_retorna_none(self):
        deal = self._deal(
            name="Projeto Igual",
            amount_total=1000,
            organization={"id": "org-1", "name": "Cliente Igual"},
            user={"name": "Vendedor Igual", "email": "igual@conticonsultoria.com.br"},
            closed_at="2026-09-01T00:00:00.000-03:00",
        )
        documento = self._documento(
            capa_projeto={
                "codigo": "Projeto Igual",
                "nome_vendedor": "Vendedor Igual",
                "email_vendedor": "igual@conticonsultoria.com.br",
            },
            cliente={"nome": "Cliente Igual", "cliente_id": "org-1"},
            formacao_preco={"valor": 1000},
            rd_closed_at="2026-09-01T00:00:00.000-03:00",
        )

        resultado = self.services.reconciliar_campos_rd(documento, deal)

        self.assertIsNone(resultado)

    def test_apenas_o_campo_divergente_aparece_no_resultado(self):
        deal = self._deal(
            amount_total=1000,
            organization={"id": "org-1", "name": "Cliente Igual"},
            user={"name": "Vendedor Igual", "email": "igual@conticonsultoria.com.br"},
            closed_at="2026-09-01T00:00:00.000-03:00",
            name="Nome Novo",
        )
        documento = self._documento(
            capa_projeto={
                "codigo": "Nome Antigo",
                "nome_vendedor": "Vendedor Igual",
                "email_vendedor": "igual@conticonsultoria.com.br",
            },
            cliente={"nome": "Cliente Igual", "cliente_id": "org-1"},
            formacao_preco={"valor": 1000},
            rd_closed_at="2026-09-01T00:00:00.000-03:00",
        )

        resultado = self.services.reconciliar_campos_rd(documento, deal)

        self.assertEqual(resultado, {"capa_projeto.codigo": "Nome Novo"})


if __name__ == "__main__":
    unittest.main()
