from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, config, datasets, diagnostics, me, models, notifications, training, vehicles
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.db.base import Base
from app.db.session import engine

# Import models so Base.metadata is populated before create_all().
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="EV Battery SoH Classification API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(config.router)
app.include_router(datasets.router)
app.include_router(training.router)
app.include_router(models.router)
app.include_router(vehicles.router)
app.include_router(diagnostics.router)
app.include_router(me.router)
app.include_router(notifications.router)
