from pydantic import BaseModel


class ProductDetail(BaseModel):
    sku: str
    name: str
    brand: str
    price: float
    color: str
    color_family: str
    category: str
    gender: str
    image_url: str
    url: str = ""
    image_urls: list[str] = []
    style_tags: list[str] = []
    materials: list[str] = []
    sizes_available: list[str] = []
    product_details: str = ""
    in_stock: bool = True


class OutfitItem(BaseModel):
    sku: str
    name: str
    brand: str
    price: float
    color_family: str
    category: str
    image_url: str
    outfit_score: float


class OutfitResponse(BaseModel):
    source: ProductDetail
    outfit: dict[str, list[OutfitItem]]


class SimilarProductItem(BaseModel):
    sku: str
    name: str
    brand: str
    price: float
    color: str
    category: str
    image_url: str
    similarity_score: float


class SimilarResponse(BaseModel):
    source: ProductDetail
    results: list[SimilarProductItem]
    total: int
