from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from backend.app.main import app


def _make_product_detail():
    return {
        "sku": "12345", "name": "Test Dress", "brand": "ASOS",
        "price": 29.99, "color_clean": "black", "color_family": "black",
        "category": "Dresses", "gender": "Women",
        "primary_image_url": "https://example.com/img.jpg",
        "image_urls": ["https://example.com/img.jpg", "https://example.com/img2.jpg"],
        "style_tags": ["casual", "summer"], "materials": ["cotton"],
        "sizes_available": ["S", "M", "L"],
        "product_details": "A nice black dress", "any_in_stock": True,
    }


class TestProductEndpoints:
    def test_product_detail(self):
        engine = MagicMock()
        engine._is_ready = True
        engine.get_product_detail.return_value = _make_product_detail()
        app.state.engine = engine

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/products/12345")
        assert response.status_code == 200
        data = response.json()
        assert data["sku"] == "12345"
        assert data["name"] == "Test Dress"
        assert len(data["image_urls"]) == 2
        assert data["materials"] == ["cotton"]

    def test_product_not_found(self):
        engine = MagicMock()
        engine._is_ready = True
        engine.get_product_detail.return_value = None
        app.state.engine = engine

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/products/99999")
        assert response.status_code == 404

    def test_outfit(self):
        engine = MagicMock()
        engine._is_ready = True
        engine.get_product_detail.return_value = _make_product_detail()
        engine.complete_the_look.return_value = {}
        app.state.engine = engine

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/products/12345/outfit")
        assert response.status_code == 200
        data = response.json()
        assert "source" in data
        assert "outfit" in data
        assert data["source"]["sku"] == "12345"

    def test_outfit_not_found(self):
        engine = MagicMock()
        engine._is_ready = True
        engine.get_product_detail.return_value = None
        app.state.engine = engine

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/products/99999/outfit")
        assert response.status_code == 404

    def test_outfit_with_categories(self):
        import pandas as pd
        engine = MagicMock()
        engine._is_ready = True
        engine.get_product_detail.return_value = _make_product_detail()
        engine.complete_the_look.return_value = {
            "Shoes": pd.DataFrame([{
                "sku": "55555", "name": "Black Heels", "brand": "ASOS",
                "price": 45.00, "color_family": "black", "category": "Shoes",
                "primary_image_url": "https://example.com/shoes.jpg",
                "outfit_score": 0.82,
            }])
        }
        app.state.engine = engine

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/products/12345/outfit")
        assert response.status_code == 200
        data = response.json()
        assert "Shoes" in data["outfit"]
        assert len(data["outfit"]["Shoes"]) == 1
        assert data["outfit"]["Shoes"][0]["outfit_score"] == 0.82
