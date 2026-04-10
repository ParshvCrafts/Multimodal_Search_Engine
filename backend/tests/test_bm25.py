import numpy as np
from backend.app.engine.bm25 import SimpleBM25


class TestSimpleBM25:
    def test_fit_and_score(self):
        bm25 = SimpleBM25()
        docs = [
            "black leather jacket mens",
            "red floral dress womens",
            "blue denim jeans casual",
        ]
        bm25.fit(docs)
        assert bm25.n_docs == 3

        scores = bm25.score_candidates("black leather", [0, 1, 2])
        assert scores[0] > scores[1]
        assert scores[0] > scores[2]

    def test_empty_query(self):
        bm25 = SimpleBM25()
        bm25.fit(["black dress", "red shoes"])
        scores = bm25.score_candidates("", [0, 1])
        assert np.all(scores == 0.0)

    def test_unknown_terms(self):
        bm25 = SimpleBM25()
        bm25.fit(["black dress"])
        scores = bm25.score_candidates("xyznotaword", [0])
        assert scores[0] == 0.0

    def test_out_of_range_index(self):
        bm25 = SimpleBM25()
        bm25.fit(["black dress"])
        scores = bm25.score_candidates("black", [0, 999])
        assert scores[0] > 0
        assert scores[1] == 0.0

    def test_exact_match_scores_higher(self):
        bm25 = SimpleBM25()
        bm25.fit(["black leather jacket", "red silk dress", "blue cotton shirt"])
        scores = bm25.score_candidates("black leather jacket", [0, 1, 2])
        assert scores[0] > scores[1]
        assert scores[0] > scores[2]

    def test_doc_frequency_computed(self):
        bm25 = SimpleBM25()
        bm25.fit(["black dress", "black shoes", "red dress"])
        assert bm25.df["black"] == 2
        assert bm25.df["dress"] == 2
        assert bm25.df["red"] == 1
