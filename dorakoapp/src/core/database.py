from contextlib import contextmanager

import psycopg2
from pgvector.psycopg2 import register_vector

from core.config import Config


class Database:
    def __init__(self, config: Config):
        self._config = config

    @contextmanager
    def connect(self, vector: bool = False):
        conn = psycopg2.connect(
            host=self._config.pg_host,
            port=self._config.pg_port,
            dbname=self._config.pg_db,
            user=self._config.pg_user,
            password=self._config.pg_password,
        )
        if vector:
            register_vector(conn)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
