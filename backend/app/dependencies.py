from fastapi import Request

from backend.app.engine.search_engine import ASOSSearchEngine
from backend.app.exceptions import EngineNotReadyError


def get_engine(request: Request) -> ASOSSearchEngine:
    """FastAPI dependency: retrieve the engine singleton from app state."""
    engine: ASOSSearchEngine = getattr(request.app.state, "engine", None)
    if engine is None or not engine._is_ready:
        raise EngineNotReadyError("Search engine is not ready")
    return engine
