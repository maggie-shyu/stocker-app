from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routers import cashflow, dashboard, export, holdings, realized, settings, stocks, transactions


settings_obj = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(title=settings_obj.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings_obj.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"ok": True}


app.include_router(settings.router)
app.include_router(stocks.router)
app.include_router(cashflow.router)
app.include_router(transactions.router)
app.include_router(holdings.router)
app.include_router(realized.router)
app.include_router(dashboard.router)
app.include_router(export.router)
