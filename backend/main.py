from fastapi import FastAPI

import models
from database import engine
from routers import renters
from routers import landlords
app = FastAPI()
models.Base.metadata.create_all(bind=engine)
app.include_router(renters.router)
app.include_router(landlords.router)

