"""
Testes de app.utils.validators.validate_static_token_query: autenticação por
token estático na query string, usada pelo webhook do RD Station (cujo
cadastro não permite headers customizados).

Carrega validators.py por caminho de arquivo, com stubs mínimos de flask,
jwt, app.config e app.extensions (não instalados/configurados neste ambiente).
Os stubs valem só durante o carregamento (patch.dict restaura sys.modules).

Rodar com: python -m unittest discover -s tests
"""
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


def _carregar_validators(static_token):
    request = types.SimpleNamespace(args={}, headers={})

    flask_stub = types.ModuleType("flask")
    flask_stub.request = request
    flask_stub.jsonify = lambda dados: dados

    jwt_exceptions_stub = types.ModuleType("jwt.exceptions")
    jwt_exceptions_stub.InvalidTokenError = Exception
    jwt_stub = types.ModuleType("jwt")
    jwt_stub.exceptions = jwt_exceptions_stub

    class _Config:
        MSAL_AUTHORITY = "https://login.example.test"
        SECRET_KEY = "segredo"
        STATIC_TOKEN = static_token

    config_stub = types.ModuleType("app.config")
    config_stub.Config = _Config

    extensions_stub = types.ModuleType("app.extensions")
    extensions_stub.redis_client = None

    stubs = {
        "flask": flask_stub,
        "jwt": jwt_stub,
        "jwt.exceptions": jwt_exceptions_stub,
        "app.config": config_stub,
        "app.extensions": extensions_stub,
    }

    caminho = Path(__file__).resolve().parents[1] / "app" / "utils" / "validators.py"
    with patch.dict(sys.modules, stubs):
        spec = importlib.util.spec_from_file_location("validators_sob_teste", caminho)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)

    return modulo, request


class TestValidateStaticTokenQuery(unittest.TestCase):
    def _chamar(self, static_token, args):
        modulo, request = _carregar_validators(static_token)
        request.args = args

        @modulo.validate_static_token_query
        def handler():
            return "ok"

        return handler()

    def test_token_correto_na_query_string_autoriza(self):
        self.assertEqual(self._chamar("segredo-123", {"token": "segredo-123"}), "ok")

    def test_token_ausente_e_rejeitado(self):
        resposta, status = self._chamar("segredo-123", {})
        self.assertEqual(status, 401)

    def test_token_incorreto_e_rejeitado(self):
        resposta, status = self._chamar("segredo-123", {"token": "errado"})
        self.assertEqual(status, 401)

    def test_token_vazio_e_rejeitado(self):
        resposta, status = self._chamar("segredo-123", {"token": ""})
        self.assertEqual(status, 401)

    def test_static_token_nao_configurado_rejeita_requisicao_sem_token(self):
        # Sem essa guarda, None == None autorizaria qualquer requisição.
        resposta, status = self._chamar(None, {})
        self.assertEqual(status, 401)

    def test_static_token_nao_configurado_rejeita_mesmo_com_token_informado(self):
        resposta, status = self._chamar(None, {"token": "None"})
        self.assertEqual(status, 401)

    def test_static_token_vazio_rejeita_token_vazio(self):
        resposta, status = self._chamar("", {"token": ""})
        self.assertEqual(status, 401)


if __name__ == "__main__":
    unittest.main()
