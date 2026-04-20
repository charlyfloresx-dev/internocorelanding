from common.security.cors_setup import setup_cors
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

import asyncio
from app.api.v1.endpoints import rates
from common.middleware import InternoCoreGlobalMiddleware
from contextlib import asynccontextmanager
from app.db.session import engine
from common.models import Base
from app.models.exchange_rate import CurrencyExchangeRate
from app.services.worker import run_daily_currency_fetch

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Start background task (Non-blocking)
    app.state.currency_worker_task = asyncio.create_task(run_daily_currency_fetch())
    
    yield
    
    # Cancel background task on shutdown
    app.state.currency_worker_task.cancel()

app = FastAPI(title="Currency Exchange Service", version="1.0.0", lifespan=lifespan)

setup_cors(app)

app.add_middleware(InternoCoreGlobalMiddleware)

app.include_router(rates.router, prefix="/api/v1/currencies", tags=["Currencies"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "currency-exchange"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
