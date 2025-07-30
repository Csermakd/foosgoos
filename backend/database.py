from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import importlib
import pkgutil

DATABASE_URL = "sqlite:///./foosball.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    import models
    # Dynamically import all models in the 'models' package
    package = importlib.import_module('models')
    for _, model_name, _ in pkgutil.iter_modules(package.__path__):
        importlib.import_module(f"models.{model_name}")
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()