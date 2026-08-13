from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from src.config import settings
from src.database import Base, engine
from src.auth.exceptions import AuthExceptionHandler
from src.exceptions import HttpExceptionHandler
from src.google.exceptions import GoogleExceptionHandler
from src.notification.exceptions import NotificationExceptionHandler

from src.auth.router import router as auth_router
from src.google.router import router as google_router
from src.notification.router import router as notification_router
from src.orders.router import router as orders_router


# --------------- APPLICATION LIFECYCLE EVENTS
@asynccontextmanager
async def lifespan(_fastapi: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield


# --------------- FASTAPI INSTANCE CONFIGURATION
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url=(
        "/openapi.json" if settings.ENVIRONMENT in ("local", "staging") else None
    ),
    lifespan=lifespan,
)


# --------------- DOMAIN ERROR HANDLERS
HttpExceptionHandler(app)
AuthExceptionHandler(app)
GoogleExceptionHandler(app)
NotificationExceptionHandler(app)


# --------------- GLOBAL REQUEST MIDDLEWARE
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# --------------- API ROUTE REGISTRATION
app.include_router(auth_router)
app.include_router(notification_router)
app.include_router(google_router)
app.include_router(orders_router)
