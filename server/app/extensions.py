from sqlalchemy.orm import scoped_session
from app.database import Base, SessionLocal
import app.database as db_module


class DbProxy:
    def __init__(self):
        self._session = scoped_session(lambda: db_module.SessionLocal())
        self.Model = Base

    @property
    def session(self):
        return self._session

    @property
    def engine(self):
        return db_module.engine

    def create_all(self):
        Base.metadata.create_all(bind=self.engine)

    def drop_all(self):
        Base.metadata.drop_all(bind=self.engine)


db = DbProxy()

__all__ = ['db']