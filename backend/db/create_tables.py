from db.db import engine, Base
from db.models import Dataset, ModelRun

Base.metadata.create_all(bind=engine)
