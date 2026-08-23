"""
Testes do cache-aside em Redis para leituras do Psoffice
(app.blueprints.psoffice.services: buscar_centros_resultado, buscar_projetos).

Usa um Redis falso em memória (sem Redis real) para validar: cache miss busca
na fonte e grava no cache; cache hit não toca a fonte; expiração força nova
busca na fonte.

Rodar com: python -m unittest discover -s tests
"""
import json
import unittest
from unittest.mock import patch, MagicMock

from app.extensions import redis_client
from app.blueprints.psoffice.services import PsofficeServices


class FakeRedis:
    """Redis falso em memória; setex ignora o TTL (expiração é simulada manualmente)."""

    def __init__(self):
        self._store = {}

    def get(self, key):
        value = self._store.get(key)
        return value.encode("utf-8") if isinstance(value, str) else value

    def setex(self, key, ttl, value):
        self._store[key] = value

    def expire_now(self, key):
        """Simula a expiração do TTL removendo a chave."""
        self._store.pop(key, None)


class TestPsofficeReadCache(unittest.TestCase):
    def setUp(self):
        self.fake_redis = FakeRedis()
        self.patcher = patch.object(redis_client, "client", self.fake_redis)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.service = PsofficeServices()

    def test_centros_resultado_cache_hit_avoids_second_http_call(self):
        fake_response = MagicMock()
        fake_response.json.return_value = [{"CR_ID": "24", "nome": "AMS"}]

        with patch(
            "app.blueprints.psoffice.services.requests.get", return_value=fake_response
        ) as mock_get:
            first = self.service.buscar_centros_resultado()
            second = self.service.buscar_centros_resultado()

        self.assertEqual(first, [{"CR_ID": "24", "nome": "AMS"}])
        self.assertEqual(second, first)
        mock_get.assert_called_once()  # segunda chamada veio do cache, não da API

    def test_centros_resultado_cache_expired_hits_source_again(self):
        fake_response = MagicMock()
        fake_response.json.return_value = [{"CR_ID": "24"}]

        with patch(
            "app.blueprints.psoffice.services.requests.get", return_value=fake_response
        ) as mock_get:
            self.service.buscar_centros_resultado()
            self.fake_redis.expire_now("psoffice:centros_resultado")
            self.service.buscar_centros_resultado()

        self.assertEqual(mock_get.call_count, 2)

    def test_projetos_cache_hit_avoids_second_sql_query(self):
        fake_rows = ([(1, "Projeto X")], ["proj_id", "codigo"])

        with patch(
            "app.blueprints.psoffice.services.db_psoffice.execute_query",
            return_value=fake_rows,
        ) as mock_execute, patch(
            "app.blueprints.psoffice.services.load_file", return_value="SELECT ..."
        ):
            first = self.service.buscar_projetos()
            second = self.service.buscar_projetos()

        self.assertEqual(first, [{"proj_id": 1, "codigo": "Projeto X"}])
        self.assertEqual(second, first)
        mock_execute.assert_called_once()


if __name__ == "__main__":
    unittest.main()
