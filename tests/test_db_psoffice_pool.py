"""
Testes do pool de conexões do Psoffice (app.extensions.DatabaseManager).

Usam um pymssql.connect falso (sem SQL Server real) para validar:
- que uma conexão é devolvida ao pool mesmo quando a query falha (sem vazar);
- que o número de conexões simultaneamente criadas nunca excede o pool_size.

Rodar com: python -m unittest discover -s tests
"""
import threading
import unittest
from unittest.mock import patch

from app.extensions import DatabaseManager


class FakeCursor:
    def __init__(self, connection, should_fail=False):
        self._connection = connection
        self._should_fail = should_fail

    def execute(self, query):
        if self._should_fail:
            # Falha "de um tiro só": simula um erro no SQL da query (a conexão
            # em si continua utilizável depois, como no SQL Server real).
            self._connection._fail_next_query = False
            raise RuntimeError("query falhou de propósito (teste)")

    def fetchall(self):
        return [(1,)]

    @property
    def description(self):
        return [("resultado",)]

    def close(self):
        pass


class FakeConnection:
    """Conexão falsa que registra se foi fechada e permite forçar falha na query."""

    _create_lock = threading.Lock()
    _created_count = 0
    _peak_concurrent = 0
    _active_count = 0

    def __init__(self):
        self.closed = False
        self._fail_next_query = False
        with FakeConnection._create_lock:
            FakeConnection._created_count += 1
            FakeConnection._active_count += 1
            FakeConnection._peak_concurrent = max(
                FakeConnection._peak_concurrent, FakeConnection._active_count
            )

    def cursor(self):
        return FakeCursor(self, should_fail=self._fail_next_query)

    def close(self):
        if not self.closed:
            self.closed = True
            with FakeConnection._create_lock:
                FakeConnection._active_count -= 1

    @classmethod
    def reset_stats(cls):
        cls._created_count = 0
        cls._peak_concurrent = 0
        cls._active_count = 0


class FakeApp:
    """Substitui a Flask app só com o que DatabaseManager.init_app precisa."""

    def __init__(self, pool_size):
        self.config = {
            "DB_PSOFFICE_CONFIG": {
                "server": "fake-server",
                "database": "fake-db",
                "username": "fake-user",
                "password": "fake-pass",
            },
            "DB_PSOFFICE_POOL_SIZE": pool_size,
        }

    # DatabaseManager.init_app usa app.config.get(...)
    def __getattr__(self, name):
        raise AttributeError(name)


class TestDatabaseManagerPool(unittest.TestCase):
    def setUp(self):
        FakeConnection.reset_stats()
        self.patcher = patch(
            "app.extensions.pymssql.connect", side_effect=lambda **kwargs: FakeConnection()
        )
        self.mock_connect = self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def _make_manager(self, pool_size=5):
        manager = DatabaseManager()
        manager.init_app(FakeApp(pool_size))
        return manager

    def test_connection_returned_to_pool_when_block_raises(self):
        """1.4: se o bloco `with get_connection()` lança exceção, a conexão volta pro pool (não vaza)."""
        manager = self._make_manager(pool_size=2)

        with self.assertRaises(RuntimeError):
            with manager.get_connection() as conn:
                conn._fail_next_query = True
                conn.cursor().execute("SELECT algo invalido")

        # A conexão deve ter voltado pro pool interno, não ter sido descartada.
        self.assertEqual(manager._pool.qsize(), 1)
        self.assertEqual(FakeConnection._created_count, 1)

        # E deve ser reutilizável na próxima chamada, sem criar uma conexão nova.
        with manager.get_connection():
            pass
        self.assertEqual(FakeConnection._created_count, 1)

    def test_execute_query_releases_connection_on_error(self):
        """Mesmo teste, mas passando pelo caminho público execute_query()."""
        manager = self._make_manager(pool_size=2)

        # Força a próxima conexão criada a falhar na query.
        original_side_effect = self.mock_connect.side_effect

        def make_failing_connection(**kwargs):
            conn = original_side_effect(**kwargs)
            conn._fail_next_query = True
            return conn

        self.mock_connect.side_effect = make_failing_connection

        with self.assertRaises(RuntimeError):
            manager.execute_query("SELECT algo invalido")

        self.assertEqual(manager._pool.qsize(), 1)
        self.assertEqual(FakeConnection._created_count, 1)

    def test_pool_never_exceeds_max_size_under_concurrency(self):
        """1.5: número de conexões simultâneas nunca excede pool_size."""
        pool_size = 3
        manager = self._make_manager(pool_size=pool_size)
        num_threads = 10
        barrier = threading.Barrier(num_threads)

        def worker():
            barrier.wait()  # maximiza a chance de sobreposição real
            with manager.get_connection() as conn:
                conn.cursor().execute("SELECT 1")

        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        self.assertLessEqual(FakeConnection._peak_concurrent, pool_size)
        self.assertLessEqual(manager._created, pool_size)


if __name__ == "__main__":
    unittest.main()
