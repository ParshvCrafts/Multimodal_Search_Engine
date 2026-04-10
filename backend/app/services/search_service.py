import base64
import io
import logging
from typing import Optional

import pandas as pd
from PIL import Image

from backend.app.engine.search_engine import ASOSSearchEngine
from backend.app.exceptions import SKUNotFoundError, InvalidQueryError
from backend.app.models.search import SearchRequest, SearchResponse, SearchResultItem, QueryInfo
from backend.app.models.product import ProductDetail, OutfitResponse, OutfitItem, SimilarProductItem, SimilarResponse

logger = logging.getLogger(__name__)


def decode_image(
    image_b64: Optional[str] = None,
    image_bytes: Optional[bytes] = None,
) -> Optional[Image.Image]:
    """Decode a base64 string or raw bytes into a PIL Image.

    Raises InvalidQueryError if decoding fails.
    Returns None when neither argument is provided.
    """
    if image_b64 is None and image_bytes is None:
        return None

    try:
        if image_b64 is not None:
            # Strip optional data-URI prefix (e.g. "data:image/jpeg;base64,")
            if "," in image_b64:
                image_b64 = image_b64.split(",", 1)[1]
            raw = base64.b64decode(image_b64)
        else:
            raw = image_bytes  # type: ignore[assignment]

        return Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as exc:
        raise InvalidQueryError(f"Could not decode image: {exc}") from exc


def _row_to_search_item(row: pd.Series) -> SearchResultItem:
    """Convert a single DataFrame row to a SearchResultItem Pydantic model.

    Handles numpy scalar types and gracefully falls back when optional
    columns are absent.
    """
    # Score: prefer hybrid_score → rrf_score → score → 0
    for score_col in ("hybrid_score", "rrf_score", "score"):
        raw_score = row.get(score_col)
        if raw_score is not None:
            try:
                score = float(raw_score)
                break
            except (TypeError, ValueError):
                continue
    else:
        score = 0.0

    # style_tags: ensure it is always a plain Python list of strings
    raw_tags = row.get("style_tags", [])
    if isinstance(raw_tags, list):
        style_tags = [str(t) for t in raw_tags]
    elif isinstance(raw_tags, str) and raw_tags:
        # Could be a JSON-serialised list stored as a string
        try:
            import ast
            parsed = ast.literal_eval(raw_tags)
            style_tags = [str(t) for t in parsed] if isinstance(parsed, list) else [raw_tags]
        except Exception:
            style_tags = [raw_tags]
    else:
        style_tags = []

    return SearchResultItem(
        sku=str(row["sku"]),
        name=str(row["name"]),
        brand=str(row["brand"]),
        price=float(row["price"]),
        color=str(row.get("color_clean", "")),
        color_family=str(row.get("color_family", "")),
        category=str(row.get("category", "")),
        gender=str(row.get("gender", "")),
        image_url=str(row.get("primary_image_url", "")),
        url=str(row.get("url", "")),
        score=score,
        style_tags=style_tags,
        in_stock=bool(row.get("any_in_stock", True)),
    )


def _row_to_product_detail(detail: dict) -> ProductDetail:
    """Convert a product detail dict (from engine.get_product_detail) to a
    ProductDetail Pydantic model.

    Coerces numpy/pandas scalars and handles image_urls being a list or not.
    """
    # image_urls
    raw_image_urls = detail.get("image_urls", [])
    if isinstance(raw_image_urls, list):
        image_urls = [str(u) for u in raw_image_urls]
    elif isinstance(raw_image_urls, str) and raw_image_urls:
        try:
            import ast
            parsed = ast.literal_eval(raw_image_urls)
            image_urls = [str(u) for u in parsed] if isinstance(parsed, list) else [raw_image_urls]
        except Exception:
            image_urls = [raw_image_urls]
    else:
        image_urls = []

    # sizes_available — always a list of strings
    raw_sizes = detail.get("sizes_available", [])
    if isinstance(raw_sizes, list):
        sizes_available = [str(s) for s in raw_sizes]
    elif isinstance(raw_sizes, str) and raw_sizes:
        try:
            import ast
            parsed = ast.literal_eval(raw_sizes)
            sizes_available = [str(s) for s in parsed] if isinstance(parsed, list) else [raw_sizes]
        except Exception:
            sizes_available = [raw_sizes]
    else:
        sizes_available = []

    # style_tags
    raw_tags = detail.get("style_tags", [])
    if isinstance(raw_tags, list):
        style_tags = [str(t) for t in raw_tags]
    elif isinstance(raw_tags, str) and raw_tags:
        try:
            import ast
            parsed = ast.literal_eval(raw_tags)
            style_tags = [str(t) for t in parsed] if isinstance(parsed, list) else [raw_tags]
        except Exception:
            style_tags = [raw_tags]
    else:
        style_tags = []

    # materials
    raw_materials = detail.get("materials", [])
    if isinstance(raw_materials, list):
        materials = [str(m) for m in raw_materials]
    elif isinstance(raw_materials, str) and raw_materials:
        try:
            import ast
            parsed = ast.literal_eval(raw_materials)
            materials = [str(m) for m in parsed] if isinstance(parsed, list) else [raw_materials]
        except Exception:
            materials = [raw_materials]
    else:
        materials = []

    return ProductDetail(
        sku=str(detail["sku"]),
        name=str(detail.get("name", "")),
        brand=str(detail.get("brand", "")),
        price=float(detail.get("price", 0.0)),
        color=str(detail.get("color_clean", "")),
        color_family=str(detail.get("color_family", "")),
        category=str(detail.get("category", "")),
        gender=str(detail.get("gender", "")),
        image_url=str(detail.get("primary_image_url", "")),
        url=str(detail.get("url", "")),
        image_urls=image_urls,
        style_tags=style_tags,
        materials=materials,
        sizes_available=sizes_available,
        product_details=str(detail.get("product_details", "")),
        in_stock=bool(detail.get("any_in_stock", True)),
    )


def search(engine: ASOSSearchEngine, request: SearchRequest) -> SearchResponse:
    """Execute a text (or multimodal) search and return a SearchResponse.

    Decodes the optional base64 image, calls the engine, converts the
    resulting DataFrame, and wraps query metadata into the response.
    """
    query_image: Optional[Image.Image] = None
    if request.image_b64:
        query_image = decode_image(image_b64=request.image_b64)

    results_df: pd.DataFrame = engine.search(
        query=request.query,
        query_image=query_image,
        top_n=request.top_n,
        text_weight=request.text_weight,
        sort_by=request.sort_by,
    )

    items = [_row_to_search_item(row) for _, row in results_df.iterrows()]

    # Extract query_info dict attached by the engine
    raw_qi: dict = results_df.attrs.get("query_info", {})
    query_info = QueryInfo(
        original_query=str(raw_qi.get("original_query", request.query)),
        processed_query=str(raw_qi.get("processed_query", request.query)),
        detected_language=str(raw_qi.get("detected_language", "en")),
        was_translated=bool(raw_qi.get("was_translated", False)),
        was_spell_corrected=bool(raw_qi.get("was_spell_corrected", False)),
        spell_suggestion=raw_qi.get("spell_suggestion"),
        parsed_category=raw_qi.get("parsed_category"),
        parsed_color=raw_qi.get("parsed_color"),
        parsed_price_range=list(raw_qi.get("parsed_price_range", [None, None])),
        parsed_gender=raw_qi.get("parsed_gender"),
        parsed_style_tags=list(raw_qi.get("parsed_style_tags", [])),
        parsed_material=raw_qi.get("parsed_material"),
        parsed_size=raw_qi.get("parsed_size"),
        parsed_exclusions=list(raw_qi.get("parsed_exclusions", [])),
        sort_by=str(raw_qi.get("sort_by", request.sort_by)),
        available_sorts=list(raw_qi.get("available_sorts", [])),
        suggested_searches=list(raw_qi.get("suggested_searches", [])),
    )

    return SearchResponse(results=items, query_info=query_info, total=len(items))


def search_by_image(
    engine: ASOSSearchEngine,
    image: Image.Image,
    top_n: int = 20,
) -> SearchResponse:
    """Execute a pure image search and return a SearchResponse.

    A minimal QueryInfo is generated because there is no text query to parse.
    """
    results_df: pd.DataFrame = engine.search_by_image(image=image, top_n=top_n)

    items = [_row_to_search_item(row) for _, row in results_df.iterrows()]

    query_info = QueryInfo(
        original_query="",
        processed_query="",
    )

    return SearchResponse(results=items, query_info=query_info, total=len(items))


def get_product_detail(engine: ASOSSearchEngine, sku: str) -> ProductDetail:
    """Fetch and return full product detail for a single SKU.

    Raises SKUNotFoundError when the SKU does not exist in the catalogue.
    """
    detail = engine.get_product_detail(sku)
    if detail is None:
        raise SKUNotFoundError(sku)

    return _row_to_product_detail(detail)


def get_similar(
    engine: ASOSSearchEngine,
    sku: str,
    top_n: int = 10,
) -> SimilarResponse:
    """Return similar products for a given SKU.

    Raises SKUNotFoundError when the source SKU does not exist.
    """
    source_detail = engine.get_product_detail(sku)
    if source_detail is None:
        raise SKUNotFoundError(sku)

    source = _row_to_product_detail(source_detail)

    results_df: pd.DataFrame = engine.search_similar(sku=sku, top_n=top_n)

    similar_items = []
    for _, row in results_df.iterrows():
        similar_items.append(
            SimilarProductItem(
                sku=str(row["sku"]),
                name=str(row.get("name", "")),
                brand=str(row.get("brand", "")),
                price=float(row.get("price", 0.0)),
                color=str(row.get("color_clean", "")),
                category=str(row.get("category", "")),
                image_url=str(row.get("primary_image_url", "")),
                similarity_score=float(row.get("similarity_score", 0.0)),
            )
        )

    return SimilarResponse(source=source, results=similar_items, total=len(similar_items))


def get_outfit(
    engine: ASOSSearchEngine,
    sku: str,
    n_per_category: int = 3,
) -> OutfitResponse:
    """Return an outfit recommendation for a given SKU.

    Raises SKUNotFoundError when the source SKU does not exist.
    """
    source_detail = engine.get_product_detail(sku)
    if source_detail is None:
        raise SKUNotFoundError(sku)

    source = _row_to_product_detail(source_detail)

    outfit_dict: dict[str, pd.DataFrame] = engine.complete_the_look(
        sku=sku, n_per_category=n_per_category
    )

    outfit: dict[str, list[OutfitItem]] = {}
    for category, df in outfit_dict.items():
        category_items = []
        for _, row in df.iterrows():
            category_items.append(
                OutfitItem(
                    sku=str(row["sku"]),
                    name=str(row.get("name", "")),
                    brand=str(row.get("brand", "")),
                    price=float(row.get("price", 0.0)),
                    color_family=str(row.get("color_family", "")),
                    category=str(row.get("category", "")),
                    image_url=str(row.get("primary_image_url", "")),
                    outfit_score=float(row.get("outfit_score", 0.0)),
                )
            )
        outfit[category] = category_items

    return OutfitResponse(source=source, outfit=outfit)
