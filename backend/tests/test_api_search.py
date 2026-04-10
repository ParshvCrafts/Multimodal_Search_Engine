from unittest.mock import MagicMock
import pandas as pd
from fastapi.testclient import TestClient

from backend.app.main import app


def _make_search_results():
    df = pd.DataFrame([{
        "sku": "12345",
        "name": "Test Dress",
        "brand": "ASOS",
        "price": 29.99,
        "color_clean": "black",
        "color_family": "black",
        "category": "Dresses",
        "gender": "Women",
        "primary_image_url": "https://example.com/img.jpg",
        "hybrid_score": 0.95,
        "style_tags": ["casual"],
        "any_in_stock": True,
    }])
    df.attrs["query_info"] = {
        "original_query": "black dress",
        "processed_query": "black dress",
        "detected_language": "en",
        "was_translated": False,
        "was_spell_corrected": False,
        "spell_suggestion": None,
        "parsed_category": "Dresses",
        "parsed_color": "black",
        "parsed_price_range": [None, None],
        "parsed_gender": None,
        "parsed_style_tags": [],
        "parsed_material": None,
        "parsed_size": None,
        "parsed_exclusions": [],
        "sort_by": "relevance",
        "available_sorts": ["relevance", "price_asc", "price_desc"],
        "suggested_searches": ["navy dresses"],
    }
    return df


def _make_mock_engine():
    engine = MagicMock()
    engine._is_ready = True
    engine.search.return_value = _make_search_results()
    return engine


class TestSearchEndpoints:
    def test_text_search(self):
        app.state.engine = _make_mock_engine()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/api/v1/search", json={"query": "black dress"})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["results"][0]["sku"] == "12345"
        assert data["results"][0]["name"] == "Test Dress"
        assert data["query_info"]["parsed_category"] == "Dresses"

    def test_search_with_params(self):
        app.state.engine = _make_mock_engine()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/api/v1/search", json={
            "query": "red shoes",
            "top_n": 5,
            "sort_by": "price_asc",
        })
        assert response.status_code == 200

    def test_empty_query_rejected(self):
        app.state.engine = _make_mock_engine()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/api/v1/search", json={"query": ""})
        assert response.status_code == 422

    def test_engine_not_ready(self):
        app.state.engine = None
        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/api/v1/search", json={"query": "dress"})
        assert response.status_code == 503

    def test_similar_search(self):
        engine = _make_mock_engine()
        engine.get_product_detail.return_value = {
            "sku": "12345", "name": "Test Dress", "brand": "ASOS",
            "price": 29.99, "color_clean": "black", "color_family": "black",
            "category": "Dresses", "gender": "Women",
            "primary_image_url": "https://example.com/img.jpg",
            "image_urls": [], "style_tags": [], "materials": [],
            "sizes_available": [], "product_details": "", "any_in_stock": True,
        }
        engine.search_similar.return_value = pd.DataFrame([{
            "sku": "67890", "name": "Similar Dress", "brand": "ASOS",
            "price": 35.00, "color_clean": "navy", "category": "Dresses",
            "primary_image_url": "https://example.com/img2.jpg",
            "similarity_score": 0.89,
        }])
        app.state.engine = engine
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/search/similar/12345")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["results"][0]["similarity_score"] == 0.89
