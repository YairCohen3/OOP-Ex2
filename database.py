import os
import shutil
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# All runtime data (database, uploaded files, attendance reports) lives in one folder.
# Locally this is the project folder, exactly as before. On Railway, set SMARTCLASS_DATA_DIR to the
# mount path of a Volume (e.g. /data) so the data survives redeploys.
DATA_DIR = Path(os.getenv("SMARTCLASS_DATA_DIR", ".")).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "smartclass.db"

# First start on an empty Volume: start from the database that ships with the project (if any),
# so existing users/courses are kept. After that the Volume copy is the only one used.
_bundled_db = Path(__file__).resolve().with_name("smartclass.db")
if not DB_PATH.exists() and _bundled_db.exists() and _bundled_db != DB_PATH:
    shutil.copy2(_bundled_db, DB_PATH)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
