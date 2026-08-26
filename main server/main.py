from fastapi import FastAPI
from psycopg_pool import AsyncConnectionPool
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await pool.open()
    yield
    await pool.close()

app = FastAPI(lifespan=lifespan)
pool = AsyncConnectionPool(
    conninfo="dbname=postgres user=postgres password=111222035",
    max_size=10,
    min_size=2,
    open=False
)















