import os, json
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, Text
from sqlalchemy.orm import sessionmaker
from pathlib import Path

engine = None
SessionLocal = None
metadata = None
events_table = None
commands_table = None

def init_db(database_url: str):
    global engine, SessionLocal, metadata, events_table, commands_table
    opts = {}
    if database_url.startswith("sqlite"):
        opts = {"connect_args": {"check_same_thread": False}}
    engine = create_engine(database_url, **opts)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    metadata = MetaData()
    events_table = Table(
        "events", metadata,
        Column("id", String, primary_key=True),
        Column("device_id", String, index=True),
        Column("payload", Text),
        Column("json_path", String, nullable=True)
    )
    commands_table = Table(
        "commands", metadata,
        Column("id", String, primary_key=True),
        Column("device_id", String, index=True),
        Column("type", String),
        Column("payload", Text),
        Column("delivered", Integer, default=0)
    )
    metadata.create_all(engine)

def get_sync_session():
    if SessionLocal is None:
        raise RuntimeError("DB not initialized")
    return SessionLocal()

def create_event(db_session, event_id: str, payload: dict, json_path: str = None):
    ins = events_table.insert().values(id=event_id, device_id=payload.get("device_id"), payload=json.dumps(payload), json_path=json_path)
    db_session.execute(ins)
    db_session.commit()

def attach_thumbnail(db_session, event_id: str, thumbnail_path: str):
    sel = events_table.select().where(events_table.c.id == event_id)
    r = db_session.execute(sel).fetchone()
    if not r:
        return False
    payload = json.loads(r.payload)
    payload["thumbnail_path"] = thumbnail_path
    upd = events_table.update().where(events_table.c.id == event_id).values(payload=json.dumps(payload))
    db_session.execute(upd)
    db_session.commit()
    return True

def fetch_and_mark_delivered(db_session, device_id: str):
    rows = db_session.execute(commands_table.select().where(commands_table.c.device_id == device_id).where(commands_table.c.delivered == 0)).fetchall()
    result = []
    ids = []
    for r in rows:
        result.append({"id": r.id, "type": r.type, "payload": json.loads(r.payload)})
        ids.append(r.id)
    if ids:
        db_session.execute(commands_table.update().where(commands_table.c.id.in_(ids)).values(delivered=1))
        db_session.commit()
    return result

def enqueue_command(db_session, device_id: str, cmd_type: str, payload: dict):
    import uuid
    cmd_id = f"cmd-{uuid.uuid4().hex[:12]}"
    ins = commands_table.insert().values(id=cmd_id, device_id=device_id, type=cmd_type, payload=json.dumps(payload), delivered=0)
    db_session.execute(ins)
    db_session.commit()
    return cmd_id
