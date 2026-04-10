from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    products: int
    engine_ready: bool


@router.get("/health", response_model=HealthResponse)
def health_check(request: Request) -> HealthResponse:
    engine = getattr(request.app.state, "engine", None)
    if engine is None or not engine._is_ready:
        return HealthResponse(status="loading", products=0, engine_ready=False)
    return HealthResponse(
        status="ok",
        products=len(engine.metadata),
        engine_ready=True,
    )


@router.get("/audit")
def audit(request: Request) -> dict:
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        return {"status": "engine_not_loaded"}
    return engine.audit()
