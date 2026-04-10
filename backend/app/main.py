import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import Settings, SearchConfig
from backend.app.exceptions import EngineNotReadyError, SKUNotFoundError, InvalidQueryError
from backend.app.engine.search_engine import ASOSSearchEngine
from backend.app.routers import health, search, products

settings = Settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("asos_search")

for _noisy in (
    "urllib3", "urllib3.connectionpool", "requests", "PIL",
    "transformers", "transformers.modeling_utils",
):
    logging.getLogger(_noisy).setLevel(logging.ERROR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load engine at startup, clean up on shutdown."""
    logger.info("Starting ASOS Search Engine...")
    config = SearchConfig.from_settings(settings)
    engine = ASOSSearchEngine(config)
    engine.load_data()
    engine.build_index()
    app.state.engine = engine
    logger.info(f"Engine ready with {len(engine.metadata):,} products")
    yield
    logger.info("Shutting down ASOS Search Engine.")


app = FastAPI(
    title="ASOS Fashion Search API",
    description="Multimodal, intent-driven semantic search engine for fashion products",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")


# Exception handlers
@app.exception_handler(EngineNotReadyError)
async def engine_not_ready_handler(request: Request, exc: EngineNotReadyError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(SKUNotFoundError)
async def sku_not_found_handler(request: Request, exc: SKUNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(InvalidQueryError)
async def invalid_query_handler(request: Request, exc: InvalidQueryError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
