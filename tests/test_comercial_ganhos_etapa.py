"""
Testes de app.blueprints.comercial.services: materialização de Ganhos como
etapa gravada em warmup_projetos (sincronização, avançar etapa e arquivar),
cobrindo as tarefas 1.1, 1.3, 2.1 e 2.2 de
openspec/changes/ganhos-vira-etapa-warmup/tasks.md.

Não há backfill: uma primeira versão tentou materializar retroativamente os
ganhos pendentes anteriores ao corte de 01/09/2026, mas a busca ao RD
Station (mesmo bounded por data) trouxe negociações que já tinham sido
tratadas por outros meios e não deveriam reaparecer como "Ganhos" - a
funcionalidade foi removida (ver design.md, decisão revisada) e os
registros que ela já havia criado em produção precisam ser limpos
manualmente (ver nota no proposal.md).

Carrega comercial/services.py (e o warmup/services.py real, do qual ele
reaproveita atualizar_warmup/get_warmup_projetos_collection) diretamente por
caminho de arquivo, com stubs mínimos para as dependências de topo não
disponíveis neste ambiente (flask, pandas, pymongo real, requests, bson,
RD Station), e uma coleção Mongo falsa em memória.

Rodar com: python -m unittest discover -s tests
"""
import copy
import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta
from pathlib import Path


class FakeCollection:
    """Coleção Mongo falsa em memória, com o mínimo de find/find_one/
    insert_one/update_one usado pelos serviços testados."""

    def __init__(self):
        self._docs = []

    @staticmethod
    def _matches(doc, query):
        for campo, condicao in (query or {}).items():
            valor = doc.get(campo)
            if isinstance(condicao, dict) and "$in" in condicao:
                if valor not in condicao["$in"]:
                    return False
            elif valor != condicao:
                return False
        return True

    def find_one(self, query):
        for doc in self._docs:
            if self._matches(doc, query):
                return copy.deepcopy(doc)
        return None

    def find(self, query=None, projection=None):
        return [copy.deepcopy(d) for d in self._docs if self._matches(d, query or {})]

    def insert_one(self, doc):
        self._docs.append(copy.deepcopy(doc))
        return types.SimpleNamespace(inserted_id=f"fake-id-{len(self._docs)}")

    @staticmethod
    def _set_dotted(doc, caminho, valor):
        """Aplica um `$set` cuja chave usa dot-notation (ex.:
        "capa_projeto.codigo") como caminho aninhado, replicando o
        comportamento real do MongoDB - em vez de gravar a chave com ponto
        literalmente no documento."""
        partes = caminho.split(".")
        alvo = doc
        for parte in partes[:-1]:
            proximo = alvo.get(parte)
            if not isinstance(proximo, dict):
                proximo = {}
                alvo[parte] = proximo
            alvo = proximo
        alvo[partes[-1]] = valor

    def update_one(self, query, update, upsert=False):
        for doc in self._docs:
            if self._matches(doc, query):
                for caminho, valor in update.get("$set", {}).items():
                    self._set_dotted(doc, caminho, valor)
                push = update.get("$push")
                if push:
                    for campo, valor in push.items():
                        doc.setdefault(campo, []).append(valor)
                return types.SimpleNamespace(modified_count=1)
        if upsert:
            novo = {}
            novo.update(query)
            for caminho, valor in update.get("$set", {}).items():
                self._set_dotted(novo, caminho, valor)
            self._docs.append(novo)
            return types.SimpleNamespace(modified_count=0, upserted_id="fake-upsert-id")
        return types.SimpleNamespace(modified_count=0)


class FakeRdServices:
    """Substitui RdServices: `chamadas` registra os argumentos de cada
    chamada; retorna `wins_janela` (sincronização pela janela de `days`).

    `deals_por_id` simula o resultado de `GET /deals/{id}` usado pela
    reconciliação: cada chamada a `buscar_deal_por_id` é registrada em
    `chamadas_deal_por_id`, e retorna `deals_por_id.get(negocio_id)` (que é
    `None`, simulando falha/deal não encontrado, quando o id não foi
    registrado no dict pelo teste)."""

    chamadas = []
    wins_janela = []
    deals_por_id = {}
    chamadas_deal_por_id = []

    def obter_negociacoes(self, win=None, closed_at_period=None, start_date=None, end_date=None):
        FakeRdServices.chamadas.append({
            "win": win, "closed_at_period": closed_at_period,
            "start_date": start_date, "end_date": end_date,
        })
        return list(FakeRdServices.wins_janela)

    def buscar_deal_por_id(self, negocio_id):
        FakeRdServices.chamadas_deal_por_id.append(negocio_id)
        return FakeRdServices.deals_por_id.get(negocio_id)


def _carregar_services_com_stubs():
    # Outros arquivos de teste (test_warmup_status_history.py) registram um
    # stub falso de "bson" em sys.modules no nível de módulo, sem limpeza -
    # quando `unittest discover` importa todos os módulos de teste antes de
    # rodar qualquer um, esse stub falso pode já estar presente aqui. Como
    # este teste precisa do bson/pymongo reais (instalados neste ambiente),
    # força uma reimportação limpa para não herdar o stub de outro arquivo.
    sys.modules.pop("bson", None)
    sys.modules.pop("pymongo", None)

    fake_mongo = types.SimpleNamespace(db=None)

    app_config_stub = types.ModuleType("app.config")
    app_config_stub.Config = object

    app_extensions_stub = types.ModuleType("app.extensions")
    app_extensions_stub.mongo = fake_mongo

    # bson/requests/pymongo estão realmente instalados neste ambiente (via
    # pymongo), então são deixados resolver para os módulos reais em vez de
    # stubados - só pandas e flask (não instalados aqui) precisam de stub.
    pandas_stub = types.ModuleType("pandas")

    flask_logger = types.SimpleNamespace(debug=lambda *a, **k: None, error=lambda *a, **k: None)
    flask_stub = types.ModuleType("flask")
    flask_stub.current_app = types.SimpleNamespace(logger=flask_logger)
    flask_stub.jsonify = lambda *a, **k: None

    datetime_util_stub = types.ModuleType("app.utils.datetime_util")

    class _FakeDatetimeServices:
        @staticmethod
        def data_anterior_ndias(days=30, data_str=None):
            from datetime import datetime as _dt, timedelta as _td
            base = _dt.today() if data_str is None else _dt.strptime(data_str, "%Y-%m-%d")
            return (base - _td(days=days)).strftime("%Y-%m-%d")

    datetime_util_stub.DatetimeServices = _FakeDatetimeServices

    for nome, modulo in {
        "app.config": app_config_stub,
        "app.extensions": app_extensions_stub,
        "pandas": pandas_stub,
        "flask": flask_stub,
        "app.utils.datetime_util": datetime_util_stub,
    }.items():
        sys.modules[nome] = modulo

    backend_root = Path(__file__).resolve().parents[1] / "app"

    # app.blueprints.rdstation.services: carregado de verdade (para
    # reaproveitar reconciliar_campos_rd tal como o código de produção, sem
    # duplicar a lógica da allowlist num fake), mas com RdServices trocado
    # pelo fake controlável pelos testes (evita chamadas HTTP reais).
    rdstation_spec = importlib.util.spec_from_file_location(
        "app.blueprints.rdstation.services", backend_root / "blueprints" / "rdstation" / "services.py"
    )
    rdstation_module = importlib.util.module_from_spec(rdstation_spec)
    rdstation_spec.loader.exec_module(rdstation_module)
    rdstation_module.RdServices = FakeRdServices
    sys.modules["app.blueprints.rdstation.services"] = rdstation_module

    # app.utils.responses: carregado de verdade (lógica simples, só precisa de flask.jsonify stubado)
    responses_spec = importlib.util.spec_from_file_location(
        "app.utils.responses", backend_root / "utils" / "responses.py"
    )
    responses_module = importlib.util.module_from_spec(responses_spec)
    responses_spec.loader.exec_module(responses_module)
    sys.modules["app.utils.responses"] = responses_module

    # app.blueprints.warmup.services: carregado de verdade, para reaproveitar
    # atualizar_warmup/get_warmup_projetos_collection tal como o código de produção.
    warmup_spec = importlib.util.spec_from_file_location(
        "app.blueprints.warmup.services", backend_root / "blueprints" / "warmup" / "services.py"
    )
    warmup_module = importlib.util.module_from_spec(warmup_spec)
    warmup_spec.loader.exec_module(warmup_module)
    sys.modules["app.blueprints.warmup.services"] = warmup_module

    # app.blueprints.comercial.services: módulo sob teste
    comercial_spec = importlib.util.spec_from_file_location(
        "app.blueprints.comercial.services", backend_root / "blueprints" / "comercial" / "services.py"
    )
    comercial_module = importlib.util.module_from_spec(comercial_spec)
    comercial_spec.loader.exec_module(comercial_module)

    return comercial_module, fake_mongo


class TestGanhosEtapa(unittest.TestCase):
    def setUp(self):
        self.services, self.fake_mongo = _carregar_services_com_stubs()
        self.fake_mongo.db = types.SimpleNamespace(
            warmup_projetos=FakeCollection(),
            system_flags=FakeCollection(),
        )
        FakeRdServices.chamadas = []
        FakeRdServices.wins_janela = []
        FakeRdServices.deals_por_id = {}
        FakeRdServices.chamadas_deal_por_id = []

    def _win(self, id_, name="Projeto X", closed_at="2026-08-15", amount_total=1000):
        return {
            "id": id_,
            "name": name,
            "win": True,
            "closed_at": closed_at,
            "amount_total": amount_total,
            "organization": {"id": "org-1", "name": "Cliente X"},
            "user": {"name": "Vendedor X", "email": "vendedor@conticonsultoria.com.br"},
        }

    # --- 1.1: sincronização materializa e não duplica ---

    def test_sincronizar_novo_ganho_materializa_uma_vez(self):
        FakeRdServices.wins_janela = [self._win("NEG-1")]

        resultado = self.services.obter_novos_ganhos(days=30)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["etapa"], "Ganhos")
        self.assertEqual(resultado[0]["status"], "Aguardando")
        self.assertEqual(resultado[0]["capa_projeto"]["codigo"], "Projeto X")

    def test_sincronizar_novamente_nao_duplica(self):
        FakeRdServices.wins_janela = [self._win("NEG-1")]

        self.services.obter_novos_ganhos(days=30)
        resultado = self.services.obter_novos_ganhos(days=30)

        docs_neg1 = [d for d in self.fake_mongo.db.warmup_projetos._docs if d["negocio_id"] == "NEG-1"]
        self.assertEqual(len(docs_neg1), 1)
        self.assertEqual(len(resultado), 1)

    def test_sincronizar_nao_reprocessa_ganho_ja_tratado(self):
        self.fake_mongo.db.warmup_projetos.insert_one({
            "negocio_id": "NEG-OLD", "etapa": "Arquivado", "status": "Arquivado",
        })
        FakeRdServices.wins_janela = [self._win("NEG-OLD", closed_at="2026-08-01")]

        self.services.obter_novos_ganhos(days=30)

        docs = [d for d in self.fake_mongo.db.warmup_projetos._docs if d["negocio_id"] == "NEG-OLD"]
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["etapa"], "Arquivado")

    # --- 1.3: listagem só retorna etapa Ganhos ---

    def test_listagem_retorna_apenas_etapa_ganhos(self):
        self.fake_mongo.db.warmup_projetos.insert_one({"negocio_id": "NEG-A", "etapa": "Ganhos", "status": "Aguardando"})
        self.fake_mongo.db.warmup_projetos.insert_one({"negocio_id": "NEG-B", "etapa": "Warmup Comercial", "status": "Aguardando"})
        self.fake_mongo.db.warmup_projetos.insert_one({"negocio_id": "NEG-C", "etapa": "Arquivado", "status": "Arquivado"})

        resultado = self.services.obter_novos_ganhos(days=30)

        etapas = {d["etapa"] for d in resultado}
        self.assertEqual(etapas, {"Ganhos"})

    # --- 2.1: avançar etapa (iniciar_warmup) ---

    def test_avancar_etapa_sem_responsavel_falha(self):
        self.fake_mongo.db.warmup_projetos.insert_one({"negocio_id": "NEG-1", "etapa": "Ganhos", "status": "Aguardando"})

        resposta, status = self.services.iniciar_warmup({"negocio_id": "NEG-1"})

        self.assertFalse(resposta["success"])
        self.assertEqual(status, 400)
        doc = self.fake_mongo.db.warmup_projetos.find_one({"negocio_id": "NEG-1"})
        self.assertEqual(doc["etapa"], "Ganhos")

    def test_avancar_etapa_com_responsavel_atualiza_registro_existente(self):
        self.fake_mongo.db.warmup_projetos.insert_one({"negocio_id": "NEG-1", "etapa": "Ganhos", "status": "Aguardando"})

        resposta, status = self.services.iniciar_warmup({
            "negocio_id": "NEG-1",
            "responsavel": "Maria Souza",
            "email_responsavel": "maria.souza@conticonsultoria.com.br",
        })

        self.assertTrue(resposta["success"])
        self.assertEqual(status, 200)
        docs = [d for d in self.fake_mongo.db.warmup_projetos._docs if d["negocio_id"] == "NEG-1"]
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["etapa"], "Warmup Comercial")
        self.assertEqual(docs[0]["responsaveis"]["responsavel_comercial"]["nome"], "Maria Souza")

    # --- 2.2: arquivar atualiza o registro existente ---

    def test_arquivar_atualiza_registro_existente(self):
        self.fake_mongo.db.warmup_projetos.insert_one({"negocio_id": "NEG-1", "etapa": "Ganhos", "status": "Aguardando"})

        resposta, status = self.services.arquivar_negociacao({"negocio_id": "NEG-1"})

        self.assertTrue(resposta["success"])
        self.assertEqual(status, 200)
        docs = [d for d in self.fake_mongo.db.warmup_projetos._docs if d["negocio_id"] == "NEG-1"]
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["etapa"], "Arquivado")
        self.assertEqual(docs[0]["status"], "Arquivado")
        self.assertIn("arquivado_em", docs[0])


class TestFakeCollectionDotNotation(unittest.TestCase):
    """Cobre a tarefa 1.2: FakeCollection precisa interpretar chaves de
    `$set` com dot-notation como caminho aninhado, replicando o
    comportamento real do MongoDB - do contrário os testes de reconciliação
    passariam com falso-positivo (gravando a chave com ponto literalmente)."""

    def test_set_dot_notation_atualiza_campo_aninhado(self):
        colecao = FakeCollection()
        colecao.insert_one({"negocio_id": "NEG-1", "capa_projeto": {"codigo": "Antigo"}})

        colecao.update_one({"negocio_id": "NEG-1"}, {"$set": {"capa_projeto.codigo": "Novo"}})

        doc = colecao.find_one({"negocio_id": "NEG-1"})
        self.assertEqual(doc["capa_projeto"]["codigo"], "Novo")
        self.assertNotIn("capa_projeto.codigo", doc)

    def test_set_dot_notation_cria_sub_objeto_ausente(self):
        colecao = FakeCollection()
        colecao.insert_one({"negocio_id": "NEG-1"})

        colecao.update_one({"negocio_id": "NEG-1"}, {"$set": {"cliente.nome": "Cliente Novo"}})

        doc = colecao.find_one({"negocio_id": "NEG-1"})
        self.assertEqual(doc["cliente"]["nome"], "Cliente Novo")

    def test_set_dot_notation_nao_afeta_outros_campos_do_sub_objeto(self):
        colecao = FakeCollection()
        colecao.insert_one({
            "negocio_id": "NEG-1",
            "capa_projeto": {"codigo": "Antigo", "gerente_projeto": {"nome": "Gerente X"}},
        })

        colecao.update_one({"negocio_id": "NEG-1"}, {"$set": {"capa_projeto.codigo": "Novo"}})

        doc = colecao.find_one({"negocio_id": "NEG-1"})
        self.assertEqual(doc["capa_projeto"]["gerente_projeto"]["nome"], "Gerente X")


class TestReconciliacaoGanhos(unittest.TestCase):
    """Cobre as tarefas 2.1, 2.2 e 2.3 de
    openspec/changes/rd-station-reconciliar-alteracoes/tasks.md."""

    def setUp(self):
        self.services, self.fake_mongo = _carregar_services_com_stubs()
        self.fake_mongo.db = types.SimpleNamespace(
            warmup_projetos=FakeCollection(),
            system_flags=FakeCollection(),
        )
        FakeRdServices.chamadas = []
        FakeRdServices.wins_janela = []
        FakeRdServices.deals_por_id = {}
        FakeRdServices.chamadas_deal_por_id = []

    def _deal(self, id_, name="Nome Atualizado", amount_total=5000, closed_at="2026-09-18"):
        return {
            "id": id_,
            "name": name,
            "amount_total": amount_total,
            "closed_at": closed_at,
            "organization": {"id": "org-1", "name": "Cliente Atualizado"},
            "user": {"name": "Vendedor Atualizado", "email": "vendedor@conticonsultoria.com.br"},
        }

    # --- 2.1: marcador ausente/expirado dispara a reconciliação ---

    def test_marcador_ausente_dispara_reconciliacao_e_cria_marcador(self):
        self.fake_mongo.db.warmup_projetos.insert_one({
            "negocio_id": "NEG-1", "etapa": "Ganhos",
            "capa_projeto": {"codigo": "Nome Antigo"},
        })
        FakeRdServices.deals_por_id = {"NEG-1": self._deal("NEG-1")}

        reconciliados = self.services.reconciliar_ganhos_pendentes()

        self.assertEqual(reconciliados, 1)
        doc = self.fake_mongo.db.warmup_projetos.find_one({"negocio_id": "NEG-1"})
        self.assertEqual(doc["capa_projeto"]["codigo"], "Nome Atualizado")
        self.assertIn("rd_reconciliado_em", doc)

        marcador = self.fake_mongo.db.system_flags.find_one({"_id": "ganhos_reconciliacao_ultima_execucao"})
        self.assertIsNotNone(marcador)
        self.assertIn("executado_em", marcador)

    def test_marcador_expirado_dispara_reconciliacao_novamente(self):
        self.fake_mongo.db.warmup_projetos.insert_one({
            "negocio_id": "NEG-1", "etapa": "Ganhos",
            "capa_projeto": {"codigo": "Nome Antigo"},
        })
        self.fake_mongo.db.system_flags.insert_one({
            "_id": "ganhos_reconciliacao_ultima_execucao",
            "executado_em": datetime.utcnow() - timedelta(minutes=31),
        })
        FakeRdServices.deals_por_id = {"NEG-1": self._deal("NEG-1")}

        reconciliados = self.services.reconciliar_ganhos_pendentes()

        self.assertEqual(reconciliados, 1)
        self.assertEqual(FakeRdServices.chamadas_deal_por_id, ["NEG-1"])

    # --- 2.2: dentro da janela não repete as buscas ---

    def test_dentro_da_janela_nao_repete_buscas(self):
        self.fake_mongo.db.warmup_projetos.insert_one({
            "negocio_id": "NEG-1", "etapa": "Ganhos",
            "capa_projeto": {"codigo": "Nome Antigo"},
        })
        self.fake_mongo.db.system_flags.insert_one({
            "_id": "ganhos_reconciliacao_ultima_execucao",
            "executado_em": datetime.utcnow() - timedelta(minutes=5),
        })
        FakeRdServices.deals_por_id = {"NEG-1": self._deal("NEG-1")}

        reconciliados = self.services.reconciliar_ganhos_pendentes()

        self.assertEqual(reconciliados, 0)
        self.assertEqual(FakeRdServices.chamadas_deal_por_id, [])
        doc = self.fake_mongo.db.warmup_projetos.find_one({"negocio_id": "NEG-1"})
        self.assertEqual(doc["capa_projeto"]["codigo"], "Nome Antigo")

    # --- 2.3: falha em um negócio não interrompe os demais ---

    def test_falha_em_um_negocio_nao_interrompe_os_demais(self):
        self.fake_mongo.db.warmup_projetos.insert_one({
            "negocio_id": "NEG-FALHA", "etapa": "Ganhos",
            "capa_projeto": {"codigo": "Nome Antigo"},
        })
        self.fake_mongo.db.warmup_projetos.insert_one({
            "negocio_id": "NEG-OK", "etapa": "Ganhos",
            "capa_projeto": {"codigo": "Nome Antigo"},
        })
        # NEG-FALHA não é registrado em deals_por_id - FakeRdServices simula
        # a falha retornando None, como o real buscar_deal_por_id faria se o
        # deal tivesse sido excluído no RD Station.
        FakeRdServices.deals_por_id = {"NEG-OK": self._deal("NEG-OK")}

        reconciliados = self.services.reconciliar_ganhos_pendentes()

        self.assertEqual(reconciliados, 1)
        self.assertEqual(set(FakeRdServices.chamadas_deal_por_id), {"NEG-FALHA", "NEG-OK"})

        doc_falha = self.fake_mongo.db.warmup_projetos.find_one({"negocio_id": "NEG-FALHA"})
        self.assertEqual(doc_falha["capa_projeto"]["codigo"], "Nome Antigo")
        doc_ok = self.fake_mongo.db.warmup_projetos.find_one({"negocio_id": "NEG-OK"})
        self.assertEqual(doc_ok["capa_projeto"]["codigo"], "Nome Atualizado")

    # --- escopo restrito à etapa Ganhos ---

    def test_documento_fora_da_etapa_ganhos_nao_e_afetado(self):
        self.fake_mongo.db.warmup_projetos.insert_one({
            "negocio_id": "NEG-1", "etapa": "Warmup Comercial",
            "capa_projeto": {"codigo": "Nome Antigo"},
        })
        FakeRdServices.deals_por_id = {"NEG-1": self._deal("NEG-1")}

        self.services.reconciliar_ganhos_pendentes()

        self.assertEqual(FakeRdServices.chamadas_deal_por_id, [])
        doc = self.fake_mongo.db.warmup_projetos.find_one({"negocio_id": "NEG-1"})
        self.assertEqual(doc["capa_projeto"]["codigo"], "Nome Antigo")

    # --- 2.4: integração via obter_novos_ganhos ---

    def test_obter_novos_ganhos_dispara_reconciliacao_do_backlog(self):
        # Ganho antigo, já materializado, fora da janela de `days` de wins
        # (não retornado por obter_negociacoes) - só a reconciliação
        # independente de janela deve alcançá-lo.
        self.fake_mongo.db.warmup_projetos.insert_one({
            "negocio_id": "NEG-ANTIGO", "etapa": "Ganhos",
            "capa_projeto": {"codigo": "Nome Antigo"},
        })
        FakeRdServices.wins_janela = []
        FakeRdServices.deals_por_id = {"NEG-ANTIGO": self._deal("NEG-ANTIGO")}

        self.services.obter_novos_ganhos(days=30)

        doc = self.fake_mongo.db.warmup_projetos.find_one({"negocio_id": "NEG-ANTIGO"})
        self.assertEqual(doc["capa_projeto"]["codigo"], "Nome Atualizado")


if __name__ == "__main__":
    unittest.main()
