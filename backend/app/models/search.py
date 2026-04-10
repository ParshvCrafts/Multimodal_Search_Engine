from typing import Literal, Optional
from pydantic import BaseModel, Field

SortOption = Literal["relevance", "price_asc", "price_desc", "name_asc", "name_desc"]


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Search query text")
    top_n: int = Field(20, ge=1, le=100, description="Number of results to return")
    sort_by: SortOption = Field("relevance", description="Sort order")
    text_weight: float = Field(0.5, ge=0.0, le=1.0, description="Text vs image weight for multimodal queries")
    image_b64: Optional[str] = Field(None, description="Base64-encoded image for multimodal search")


class SearchResultItem(BaseModel):
    sku: str
    name: str
    brand: str
    price: float
    color: str
    color_family: str
    category: str
    gender: str
    image_url: str
    url: Optional[str] = None
    score: float
    style_tags: list[str] = []
    in_stock: bool = True


class QueryInfo(BaseModel):
    original_query: str
    processed_query: str
    detected_language: str = "en"
    was_translated: bool = False
    was_spell_corrected: bool = False
    spell_suggestion: Optional[str] = None
    parsed_category: Optional[str] = None
    parsed_color: Optional[str] = None
    parsed_price_range: list[Optional[float]] = [None, None]
    parsed_gender: Optional[str] = None
    parsed_style_tags: list[str] = []
    parsed_material: Optional[str] = None
    parsed_size: Optional[str] = None
    parsed_exclusions: list[str] = []
    sort_by: str = "relevance"
    available_sorts: list[str] = []
    suggested_searches: list[str] = []


class SearchResponse(BaseModel):
    results: list[SearchResultItem]
    query_info: QueryInfo
    total: int


class ImageSearchRequest(BaseModel):
    top_n: int = Field(20, ge=1, le=100)


class EvaluateRequest(BaseModel):
    test_queries: list[dict]
    k_values: list[int] = [5, 10, 20]
