import os
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.config import settings

connect_args = {}
pool_kwargs = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    if ":memory:" in settings.DATABASE_URL:
        pool_kwargs["poolclass"] = StaticPool
else:
    pool_kwargs["pool_pre_ping"] = True
    pool_kwargs["pool_recycle"] = 300

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    **pool_kwargs,
)

if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

class ModelBase:
    def save(self):
        from app.extensions import db
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        from app.extensions import db
        db.session.delete(self)
        db.session.commit()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base(cls=ModelBase)


def configure_engine(database_url: str | None = None):
    global engine, SessionLocal
    url = database_url or settings.DATABASE_URL
    args = {}
    kwargs = {}
    if url.startswith("sqlite"):
        args["check_same_thread"] = False
        if ":memory:" in url:
            kwargs["poolclass"] = StaticPool
    else:
        kwargs["pool_pre_ping"] = True
        kwargs["pool_recycle"] = 300

    engine = create_engine(url, connect_args=args, **kwargs)
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    SessionLocal.configure(bind=engine)
    return engine


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
