from fastapi import FastAPI, HTTPException, status
from contextlib import asynccontextmanager
import asyncpg
from pgvector.asyncpg import register_vector
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio
from typing import Optional
from cache import red, RedisError, ping
from pydantic import BaseModel
from search import search
from config import DSN
from fastapi.middleware.cors import CORSMiddleware

pool: Optional[asyncpg.Pool] = None

#Backoff for retrying, exponential retries
@retry(stop=stop_after_attempt(4),wait=wait_exponential(multiplier=1, min=2, max=30))
async def make_pool():
    # Initialize pool
    pool = await asyncpg.create_pool(dsn=DSN, init=register_vector)
    return pool

#Pool Initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    #attach to app state
    global pool
    pool = await make_pool()
    app.state.pool = pool
    yield
    # Shutdown pool
    await pool.close()
    app.state.pool = None

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    #* is being utilized for testing, dont allow ALL connections
    #Will change to frontend hosting url
    allow_origins=["*"],
    allow_methods=["*"]
)

'''
Cross Origin Resource Sharing
Key CORS Headers:
Access-Control-Allow-Origin
Access-Control-Allow-Methods
Access-Control-Allow-Headers
Access-Control-Allow-Credentials
'''

@app.get("/")
async def root():
    return {"Cinemantic": "Semantic Search Engine for Movie Recommendations"}

class SearchRequest(BaseModel):
    query: str
    year: int | None = None
    runtime: int = None
    min_rating: float = None

@app.post("/search")
async def search_post(request: SearchRequest):
    async with pool.acquire() as conn:
        search_conn = await search(conn, request.query, request.year, request.runtime, request.min_rating)
        return search_conn

@app.get("/health")
async def health():
    results = {"Redis": "", "Postgresql": ""}
    try:
        red.ping()
        results["Redis"] = True
    except (RedisError, OSError):
        results["Redis"] = False
    if pool is not None:
        try:
            await asyncio.wait_for(pool.fetchval("SELECT 1"), timeout=2.0)
            results["Postgresql"] = True
        except (asyncio.TimeoutError, OSError, asyncpg.PostgresError):
            results["Postgresql"] = False
        if results["Redis"] is not True or results["Postgresql"] is not True:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=results)
    else:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=results)
    return results


    