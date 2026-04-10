import logging
from typing import List, Optional, Tuple

import numpy as np
import faiss

from backend.app.config import SearchConfig

logger = logging.getLogger(__name__)


class DualFAISSIndex:
    """
    Two parallel FAISS indices (image + text) fused via Reciprocal Rank Fusion.
    """

    def __init__(self, dim: int, config: SearchConfig):
        self.dim = dim
        self.config = config
        self.image_index = None
        self.text_index = None

    def _create_index(self, n_vectors: int) -> faiss.Index:
        if n_vectors < 5000:
            logger.info(f"Using IndexFlatIP (exact, n={n_vectors:,})")
            return faiss.IndexFlatIP(self.dim)

        n_clusters = min(self.config.n_clusters, max(16, n_vectors // 40))
        logger.info(f"Using IndexIVFFlat (n={n_vectors:,}, clusters={n_clusters})")
        quantizer = faiss.IndexFlatIP(self.dim)
        index = faiss.IndexIVFFlat(
            quantizer, self.dim, n_clusters, faiss.METRIC_INNER_PRODUCT
        )
        return index

    def build(self, image_embeddings: np.ndarray, text_embeddings: np.ndarray):
        image_embeddings = image_embeddings.astype(np.float32)
        text_embeddings = text_embeddings.astype(np.float32)

        assert image_embeddings.shape == text_embeddings.shape, (
            f"Shape mismatch: images {image_embeddings.shape} vs text {text_embeddings.shape}"
        )

        n = image_embeddings.shape[0]

        logger.info("Building image FAISS index...")
        self.image_index = self._create_index(n)
        if hasattr(self.image_index, 'train'):
            try:
                self.image_index.train(image_embeddings)
            except Exception:
                self.image_index = faiss.IndexFlatIP(self.dim)
        self.image_index.add(image_embeddings)

        logger.info("Building text FAISS index...")
        self.text_index = self._create_index(n)
        if hasattr(self.text_index, 'train'):
            try:
                self.text_index.train(text_embeddings)
            except Exception:
                self.text_index = faiss.IndexFlatIP(self.dim)
        self.text_index.add(text_embeddings)

        logger.info(
            f"Dual index built: {self.image_index.ntotal:,} image, "
            f"{self.text_index.ntotal:,} text vectors"
        )

    def search_image_index(self, query: np.ndarray, top_k: int):
        q = query.astype(np.float32).reshape(1, -1)
        if hasattr(self.image_index, 'nprobe'):
            self.image_index.nprobe = self.config.n_probe
        return self.image_index.search(q, top_k)

    def search_text_index(self, query: np.ndarray, top_k: int):
        q = query.astype(np.float32).reshape(1, -1)
        if hasattr(self.text_index, 'nprobe'):
            self.text_index.nprobe = self.config.n_probe
        return self.text_index.search(q, top_k)

    def search_fused(
        self, query: np.ndarray, top_k: int,
        image_weight: Optional[float] = None,
        text_weight: Optional[float] = None,
    ) -> Tuple[List[int], List[float]]:
        iw = image_weight or self.config.image_index_weight
        tw = text_weight or self.config.text_index_weight
        rrf_k = self.config.rrf_k

        broad_k = min(top_k * 3, self.image_index.ntotal)

        _, img_ids = self.search_image_index(query, broad_k)
        _, txt_ids = self.search_text_index(query, broad_k)
        img_ids = img_ids[0]
        txt_ids = txt_ids[0]

        img_rank = {int(idx): rank + 1 for rank, idx in enumerate(img_ids) if idx >= 0}
        txt_rank = {int(idx): rank + 1 for rank, idx in enumerate(txt_ids) if idx >= 0}

        all_candidates = set(img_rank.keys()) | set(txt_rank.keys())
        scores = {}
        for idx in all_candidates:
            score = 0.0
            if idx in img_rank:
                score += iw / (rrf_k + img_rank[idx])
            if idx in txt_rank:
                score += tw / (rrf_k + txt_rank[idx])
            scores[idx] = score

        ranked = sorted(scores.items(), key=lambda x: -x[1])[:top_k]
        return [r[0] for r in ranked], [r[1] for r in ranked]

    def save(self, image_path: str, text_path: str):
        faiss.write_index(self.image_index, image_path)
        faiss.write_index(self.text_index, text_path)
        logger.info(f"Saved dual index to {image_path} and {text_path}")

    def load(self, image_path: str, text_path: str):
        self.image_index = faiss.read_index(image_path)
        self.text_index = faiss.read_index(text_path)
        logger.info(
            f"Loaded dual index: {self.image_index.ntotal:,} image, "
            f"{self.text_index.ntotal:,} text vectors"
        )


__all__ = ["DualFAISSIndex"]
