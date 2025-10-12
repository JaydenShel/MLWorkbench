from db import engine, Base
from models import Dataset, ModelRun

Base.metadata.create_all(bind=engine)
