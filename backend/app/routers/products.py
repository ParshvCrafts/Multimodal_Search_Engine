from fastapi import APIRouter, Depends, Query

from backend.app.dependencies import get_engine
from backend.app.engine.search_engine import ASOSSearchEngine
from backend.app.models.product import ProductDetail, OutfitResponse
from backend.app.services import search_service

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/{sku}", response_model=ProductDetail)
def product_detail(
    sku: str,
    engine: ASOSSearchEngine = Depends(get_engine),
) -> ProductDetail:
    """Get full product details for a single SKU."""
    return search_service.get_product_detail(engine, sku)


@router.get("/{sku}/outfit", response_model=OutfitResponse)
def complete_the_look(
    sku: str,
    n_per_category: int = Query(3, ge=1, le=10),
    engine: ASOSSearchEngine = Depends(get_engine),
) -> OutfitResponse:
    """Get outfit recommendations for a product."""
    return search_service.get_outfit(engine, sku, n_per_category=n_per_category)
