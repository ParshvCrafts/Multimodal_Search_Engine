"""ASOS Search Engine core modules."""


def __getattr__(name):
    if name == "ASOSSearchEngine":
        from backend.app.engine.search_engine import ASOSSearchEngine
        return ASOSSearchEngine
    if name == "SearchEvaluator":
        from backend.app.engine.evaluator import SearchEvaluator
        return SearchEvaluator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["ASOSSearchEngine", "SearchEvaluator"]
