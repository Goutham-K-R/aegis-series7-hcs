from aegis.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from aegis.storage.orm import FactORM, ValidityORM, EntityORM
engine = create_engine(settings.db_url)
with sessionmaker(bind=engine)() as session:
    for f in session.query(FactORM).all():
        subj = session.query(EntityORM).get(f.subject_id)
        val = session.query(ValidityORM).get(f.validity_id) if f.validity_id else None
        s_name = subj.canonical_name if subj else "Unknown"
        vmin = val.fw_version_min if val else None
        vmax = val.fw_version_max if val else None
        print(f'{s_name} {f.predicate}: {f.value} [FW min: {vmin}, max: {vmax}]')
