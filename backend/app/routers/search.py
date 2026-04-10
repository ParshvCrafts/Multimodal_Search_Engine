import logging

from fastapi import APIRouter, Depends, File, Query, UploadFile

from backend.app.dependencies import get_engine
from backend.app.engine.search_engine import ASOSSearchEngine
from backend.app.models.search import (
    SearchRequest, SearchResponse, EvaluateRequest,
)
from backend.app.models.product import SimilarResponse
from backend.app.services import search_service

logger = logging.getLogger("asos_search")

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def text_search(
    request: SearchRequest,
    engine: ASOSSearchEngine = Depends(get_engine),
) -> SearchResponse:
    """Text search with optional base64 image for multimodal queries."""
    return search_service.search(engine, request)


@router.post("/image", response_model=SearchResponse)
async def image_search(
    file: UploadFile = File(...),
    top_n: int = Query(20, ge=1, le=100),
    engine: ASOSSearchEngine = Depends(get_engine),
) -> SearchResponse:
    """Image-only search via file upload."""
    image_bytes = await file.read()
    image = search_service.decode_image(image_bytes=image_bytes)
    if image is None:
        from backend.app.exceptions import InvalidQueryError
        raise InvalidQueryError("Uploaded file could not be decoded as an image")
    return search_service.search_by_image(engine, image, top_n=top_n)


@router.get("/similar/{sku}", response_model=SimilarResponse)
def similar_search(
    sku: str,
    top_n: int = Query(10, ge=1, le=100),
    engine: ASOSSearchEngine = Depends(get_engine),
) -> SimilarResponse:
    """Find visually similar products to a given SKU."""
    return search_service.get_similar(engine, sku, top_n=top_n)


@router.post("/evaluate")
def evaluate(
    request: EvaluateRequest,
    engine: ASOSSearchEngine = Depends(get_engine),
) -> dict:
    """Run evaluation suite against the engine."""
    from backend.app.engine.evaluator import SearchEvaluator
    evaluator = SearchEvaluator(engine)
    return evaluator.evaluate(request.test_queries, k_values=request.k_values)
