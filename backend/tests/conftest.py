import pytest


@pytest.fixture
def query_parser():
    from backend.app.engine.query_parser import QueryParser
    return QueryParser()
