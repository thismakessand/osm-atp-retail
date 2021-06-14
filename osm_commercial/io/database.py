import logging

from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine, MetaData


class GeoDB:
    _base = None

    def __init__(
        self,
        host: str,
        database: str,
        username: str,
        password: str,
        port: int = 5432,
        echo: bool = False,
    ):

        self.engine = create_engine(
            f"postgresql://{username}:{password}@{host}:{port}/{database}", echo=echo
        )

    @property
    def base(self):
        # only reflect metadata if called on, can get slow on large dbs
        if not self._base:
            meta = MetaData()
            meta.reflect(bind=self.engine)

            # get class from reflected metadata
            self._base = automap_base(metadata=meta)
            self._base.prepare()

        return self._base

    def test_connection(self):
        logging.info("Testing database connection...")
        with self.engine.connect():
            logging.info("Database connection OK")
