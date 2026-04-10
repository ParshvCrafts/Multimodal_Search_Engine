class EngineNotReadyError(Exception):
    """Raised when the search engine hasn't finished loading."""
    pass


class SKUNotFoundError(Exception):
    """Raised when a requested SKU doesn't exist."""

    def __init__(self, sku: str):
        self.sku = sku
        super().__init__(f"SKU '{sku}' not found")


class InvalidQueryError(Exception):
    """Raised when a search query is invalid."""
    pass
