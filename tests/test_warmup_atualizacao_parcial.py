"""
Testes de app.blueprints.warmup.services.atualizar_warmup /
montar_set_parcial: seções enviadas são mescladas ao documento, preservando
as chaves não enviadas (ex.: atividades do Serviço quando o Comercial salva
o formulário novamente).

Reaproveita o carregamento com stubs e a coleção falsa em memória de
test_warmup_status_history.

Rodar com: python -m unittest discover -s tests
"""
import copy
import types
import unittest

from test_warmup_status_history import FakeWarmupProjetosCollection, fake_mongo, services


class TestMontarSetParcial(unittest.TestCase):
    def test_secao_e_achatada_um_nivel(self):
        resultado = services.montar_set_parcial(
            {"cronograma_execucao": {"cronograma_fisico": "Project", "atividades": [{"nome": "A"}]}},
            {"cronograma_execucao": {}},
        )
        self.assertEqual(
            resultado,
            {
                "cronograma_execucao.cronograma_fisico": "Project",
                "cronograma_execucao.atividades": [{"nome": "A"}],
            },
        )

    def test_secao_vazia_nao_gera_operacao(self):
        self.assertEqual(
            services.montar_set_parcial({"adicionais_projeto": {}}, {"adicionais_projeto": {"pedido_compra": "Sim"}}),
            {},
        )

    def test_chave_dot_notation_passa_direto_e_tem_precedencia(self):
        resultado = services.montar_set_parcial(
            {
                "capa_projeto": {"gerente_projeto": {"nome": "X"}, "codigo": "C1"},
                "capa_projeto.gerente_projeto": {"nome": "Y"},
            },
            {"capa_projeto": {}},
        )
        self.assertEqual(resultado["capa_projeto.gerente_projeto"], {"nome": "Y"})
        self.assertEqual(resultado["capa_projeto.codigo"], "C1")

    def test_escalares_e_listas_ficam_como_estao(self):
        resultado = services.montar_set_parcial({"etapa": "Warmup Financeiro", "observacoes_gerais": [1, 2]})
        self.assertEqual(resultado, {"etapa": "Warmup Financeiro", "observacoes_gerais": [1, 2]})

    def test_secao_nao_objeto_no_documento_e_gravada_inteira(self):
        resultado = services.montar_set_parcial(
            {"cronograma_execucao": {"cronograma_fisico": "Project"}, "cronograma_execucao.aprovador": "Z"},
            {"cronograma_execucao": None},
        )
        self.assertEqual(resultado, {"cronograma_execucao": {"cronograma_fisico": "Project", "aprovador": "Z"}})


class TestAtualizarWarmupParcial(unittest.TestCase):
    def setUp(self):
        self.documento = {
            "negocio_id": "NEG-1",
            "status": "Liberado",
            "etapa": "Warmup Comercial",
            "status_historico": [],
            "capa_projeto": {
                "codigo": "106.7232",
                "centro_resultado": {"CR_ID": "6", "NOME": "Consultoria ERP RM"},
                "socio_responsavel": {"nome": "Antigo", "email": "antigo@x.com", "extra": "1"},
            },
            "cronograma_execucao": {
                "aprovacao_primeiro_nivel": "Não",
                "cronograma_fisico": "Cadastro de Atividades",
                "Parametrizar_agile": "Sim",
                "caminho_project": "\\\\srv\\projeto.mpp",
                "atividades": [
                    {"nome": "Levantamento", "recurso": "Consultor", "valor": "10"},
                    {"nome": "Parametrização", "recurso": "Consultor", "valor": "20"},
                    {"nome": "Treinamento", "recurso": "Consultor", "valor": "5"},
                ],
            },
            "adicionais_projeto": {"pedido_compra": "Sim"},
            "observacoes_gerais": [{"texto": "antiga"}],
        }
        self.fake_collection = FakeWarmupProjetosCollection(self.documento)
        fake_mongo.db = types.SimpleNamespace(warmup_projetos=self.fake_collection)

    def _doc(self):
        return self.fake_collection._doc

    def test_payload_do_comercial_preserva_dados_do_servico(self):
        # Formato exato do payload do Comercial que apagou as atividades (caso Strata).
        services.atualizar_warmup(
            "NEG-1",
            {
                "cronograma_execucao": {
                    "aprovacao_primeiro_nivel": "Não",
                    "aprovador": "",
                    "previsao_inicio": "2026-09-01",
                    "previsao_termino": "2026-11-30",
                    "cronograma_fisico": "Cadastro de Atividades",
                    "informar_atividades": "",
                    "selecionados": [],
                    "horas_alocadas": [],
                },
                "adicionais_projeto": {},
            },
        )

        cronograma = self._doc()["cronograma_execucao"]
        self.assertEqual(cronograma["previsao_inicio"], "2026-09-01")
        self.assertEqual(cronograma["atividades"], self.documento["cronograma_execucao"]["atividades"])
        self.assertEqual(cronograma["Parametrizar_agile"], "Sim")
        self.assertEqual(cronograma["caminho_project"], "\\\\srv\\projeto.mpp")
        self.assertEqual(self._doc()["adicionais_projeto"], {"pedido_compra": "Sim"})

    def test_chave_enviada_substitui_lista_inteira(self):
        novas = [{"nome": "A", "recurso": "R", "valor": "1"}, {"nome": "B", "recurso": "R", "valor": "2"}]
        services.atualizar_warmup("NEG-1", {"cronograma_execucao": {"atividades": novas}})
        self.assertEqual(self._doc()["cronograma_execucao"]["atividades"], novas)

    def test_objeto_aninhado_e_substituido_sem_merge_profundo(self):
        services.atualizar_warmup(
            "NEG-1", {"capa_projeto": {"socio_responsavel": {"nome": "Novo", "email": "novo@x.com"}}}
        )
        capa = self._doc()["capa_projeto"]
        self.assertEqual(capa["socio_responsavel"], {"nome": "Novo", "email": "novo@x.com"})
        self.assertEqual(capa["codigo"], "106.7232")
        self.assertEqual(capa["centro_resultado"], self.documento["capa_projeto"]["centro_resultado"])

    def test_secao_vazia_nao_altera_nada(self):
        modificados = services.atualizar_warmup("NEG-1", {"adicionais_projeto": {}})
        self.assertEqual(modificados, 0)
        self.assertEqual(self._doc(), self.documento)

    def test_limpeza_explicita_com_valor_vazio(self):
        services.atualizar_warmup("NEG-1", {"cronograma_execucao": {"caminho_project": ""}})
        cronograma = self._doc()["cronograma_execucao"]
        self.assertEqual(cronograma["caminho_project"], "")
        self.assertEqual(cronograma["Parametrizar_agile"], "Sim")

    def test_chave_dot_notation_atualiza_um_caminho(self):
        gerente = {"nome": "Michelle Nunes", "email": "m@x.com"}
        services.atualizar_warmup("NEG-1", {"capa_projeto.gerente_projeto": gerente})
        capa = self._doc()["capa_projeto"]
        self.assertEqual(capa["gerente_projeto"], gerente)
        self.assertEqual(capa["codigo"], "106.7232")

    def test_lista_de_topo_e_substituida(self):
        services.atualizar_warmup("NEG-1", {"observacoes_gerais": [{"texto": "nova"}]})
        self.assertEqual(self._doc()["observacoes_gerais"], [{"texto": "nova"}])

    def test_transicao_de_etapa_continua_gravando_historico(self):
        services.atualizar_warmup("NEG-1", {"etapa": "Warmup Financeiro", "status": "Revisado"})
        self.assertEqual(self._doc()["etapa"], "Warmup Financeiro")
        self.assertEqual(self._doc()["status_historico"][-1]["status"], "Revisado")

    def test_secao_ausente_e_criada(self):
        del self.fake_collection._doc["adicionais_projeto"]
        services.atualizar_warmup("NEG-1", {"adicionais_projeto": {"pedido_compra": "Não"}})
        self.assertEqual(self._doc()["adicionais_projeto"], {"pedido_compra": "Não"})

    def test_secao_null_e_criada(self):
        self.fake_collection._doc["cronograma_execucao"] = None
        services.atualizar_warmup("NEG-1", {"cronograma_execucao": {"cronograma_fisico": "Project"}})
        self.assertEqual(self._doc()["cronograma_execucao"], {"cronograma_fisico": "Project"})

    def test_payload_nao_e_mutado(self):
        payload = {"cronograma_execucao": {"cronograma_fisico": "Project"}, "cronograma_execucao.aprovador": "Z"}
        original = copy.deepcopy(payload)
        self.fake_collection._doc["cronograma_execucao"] = None
        services.atualizar_warmup("NEG-1", payload)
        self.assertEqual(payload, original)


if __name__ == "__main__":
    unittest.main()
