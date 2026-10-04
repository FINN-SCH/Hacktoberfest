from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlmodel import Session as DBSession
from sqlmodel import SQLModel, create_engine, select

from . import models


def make_engine(db_path: str) -> Engine:
    url = "sqlite://" if db_path == ":memory:" else f"sqlite:///{db_path}"
    kwargs = {"connect_args": {"check_same_thread": False}}
    if db_path == ":memory:":
        from sqlalchemy.pool import StaticPool

        kwargs["poolclass"] = StaticPool
    engine = create_engine(url, **kwargs)

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    return engine


def init_db(engine: Engine) -> None:
    SQLModel.metadata.create_all(engine)
    _fail_interrupted_turns(engine)


def _fail_interrupted_turns(engine: Engine) -> None:
    """A turn left in `processing` by a crash/restart can never finish; mark it failed so it is retryable."""
    with DBSession(engine) as db:
        stuck = db.exec(select(models.Turn).where(models.Turn.correction_status == "processing")).all()
        for turn in stuck:
            turn.correction_status = "stt_failed" if turn.transcript is None else "analysis_failed"
            turn.failure_code = "interrupted"
            turn.updated_at = models.utcnow()
            db.add(turn)
        finalizing = db.exec(select(models.Session).where(models.Session.status == "finalizing")).all()
        for s in finalizing:
            s.status = "active"
            db.add(s)
        db.commit()


def session_scope(engine: Engine) -> Iterator[DBSession]:
    with DBSession(engine) as db:
        yield db
