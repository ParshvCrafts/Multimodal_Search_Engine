__all__ = ["ASOSSearchEngine"]

import ast
import logging
import time
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Set

import numpy as np
import pandas as pd
from PIL import Image
from tqdm.auto import tqdm

from backend.app.config import SearchConfig
from backend.app.engine.encoder import FashionCLIPEncoder
from backend.app.engine.index import DualFAISSIndex
from backend.app.engine.query_parser import QueryParser, ParsedQuery
from backend.app.engine.bm25 import SimpleBM25
from backend.app.engine.nlp import MultilingualHandler, SpellCorrector
from backend.app.exceptions import EngineNotReadyError, SKUNotFoundError
from backend.app.engine import reranker

logger = logging.getLogger(__name__)


class ASOSSearchEngine:
    """
    v3.3 — Multimodal + multilingual fashion search engine.

    build_index() encodes ALL product text in ~3-5 min (no image downloading).
    Both FAISS indices (image + text) are populated from text embeddings.
    Image URLs from metadata are preserved for website card display.

    New in v3.1:
      - Multilingual query support (auto-detect + translate)
      - Spell correction for typos
      - Fixed SKU type handling (int/str agnostic)
      - Fixed color filter case matching

    New in v3.3:
      - Style-coherent Complete the Look outfit recommendations
      - Improved suggested related searches
      - Size-aware filtering
      - Material/fabric filtering
      - Negative/exclusion query support
    """

    # ── Outfit category pairings for "Complete the Look" ──
    OUTFIT_PAIRS = {
        'Dresses': ['Shoes', 'Coats & Jackets', 'Bags', 'Accessories'],
        'Tops': ['Trousers', 'Jeans', 'Skirts', 'Shoes', 'Accessories'],
        'Knitwear': ['Trousers', 'Jeans', 'Skirts', 'Shoes'],
        'Hoodies & Sweatshirts': ['Trousers', 'Jeans', 'Shoes', 'Accessories'],
        'Coats & Jackets': ['Tops', 'Trousers', 'Jeans', 'Shoes', 'Accessories'],
        'Trousers': ['Tops', 'Knitwear', 'Shoes', 'Coats & Jackets', 'Accessories'],
        'Jeans': ['Tops', 'Knitwear', 'Shoes', 'Coats & Jackets', 'Accessories'],
        'Shorts': ['Tops', 'Shoes', 'Accessories'],
        'Skirts': ['Tops', 'Knitwear', 'Shoes', 'Accessories'],
        'Shoes': ['Bags', 'Accessories'],
        'Suits & Tailoring': ['Tops', 'Shoes', 'Accessories'],
        'Swimwear': ['Shoes', 'Accessories', 'Bags'],
        'Jumpsuits & Playsuits': ['Shoes', 'Coats & Jackets', 'Bags', 'Accessories'],
        'Bags': ['Shoes', 'Accessories'],
        'Accessories': ['Bags', 'Shoes'],
    }

    # Colors that pair well together for outfit coherence
    COLOR_HARMONY = {
        'black': ['white', 'red', 'pink', 'grey', 'navy', 'beige', 'multi'],
        'white': ['black', 'navy', 'blue', 'beige', 'pink', 'red'],
        'navy': ['white', 'beige', 'grey', 'pink', 'red', 'brown'],
        'blue': ['white', 'navy', 'beige', 'brown', 'grey'],
        'red': ['black', 'white', 'navy', 'grey', 'beige'],
        'pink': ['black', 'white', 'navy', 'grey', 'beige', 'blue'],
        'green': ['white', 'beige', 'brown', 'navy', 'black'],
        'grey': ['black', 'white', 'navy', 'pink', 'blue', 'red'],
        'brown': ['white', 'beige', 'navy', 'green', 'blue'],
        'beige': ['navy', 'brown', 'white', 'black', 'blue', 'green'],
        'yellow': ['navy', 'white', 'grey', 'black', 'blue'],
        'orange': ['navy', 'white', 'black', 'brown', 'beige'],
        'purple': ['white', 'black', 'grey', 'beige', 'pink'],
        'burgundy': ['black', 'white', 'navy', 'beige', 'grey'],
        'khaki': ['white', 'navy', 'brown', 'black', 'beige'],
        'multi': ['black', 'white', 'navy', 'beige'],
    }

    # ── Sort options for frontend ──
    SORT_OPTIONS = {
        'relevance': ('hybrid_score', False),    # highest relevance first
        'price_asc': ('price', True),            # cheapest first
        'price_desc': ('price', False),           # most expensive first
        'name_asc': ('name', True),              # alphabetical A-Z
        'name_desc': ('name', False),            # alphabetical Z-A
    }

    def __init__(self, config: SearchConfig):
        self.config = config
        self.encoder: Optional[FashionCLIPEncoder] = None
        self.dual_index: Optional[DualFAISSIndex] = None
        self.metadata: Optional[pd.DataFrame] = None
        self.image_embeddings: Optional[np.ndarray] = None
        self.text_embeddings: Optional[np.ndarray] = None
        self.bm25: Optional[SimpleBM25] = None
        self.query_parser = QueryParser()
        self.multilingual = MultilingualHandler()
        self.spell_corrector = SpellCorrector()
        self._is_ready = False

    def load_data(self, path: Optional[str] = None):
        path = path or self.config.data_path
        logger.info(f"Loading metadata: {path}")

        if path.endswith('.parquet'):
            self.metadata = pd.read_parquet(path)
        else:
            self.metadata = pd.read_csv(path)

        list_cols = ['style_tags', 'materials', 'image_urls',
                     'sizes_available', 'sizes_out_of_stock']
        for col in list_cols:
            if col in self.metadata.columns and self.metadata[col].dtype == object:
                self.metadata[col] = self.metadata[col].apply(
                    lambda x: ast.literal_eval(x)
                    if isinstance(x, str) and x.startswith('[') else (
                        x if isinstance(x, list) else []
                    )
                )

        required = ['sku', 'name', 'price', 'primary_image_url', 'search_text']
        missing = [c for c in required if c not in self.metadata.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # ── Normalize SKU to string for consistent lookups ──
        self.metadata['sku'] = self.metadata['sku'].astype(str)

        # ── Normalize color_family to lowercase for consistent filtering ──
        if 'color_family' in self.metadata.columns:
            self.metadata['color_family'] = self.metadata['color_family'].str.lower().str.strip()

        self.metadata = self.metadata.reset_index(drop=True)
        logger.info(f"Loaded {len(self.metadata):,} products")

    def build_index(self, force_rebuild: bool = False):
        """
        Build search index from text only. ~3-5 min for 30K products.
        """
        img_emb_path = Path(self.config.image_embeddings_path)
        txt_emb_path = Path(self.config.text_embeddings_path)
        img_idx_path = Path(self.config.image_index_path)
        txt_idx_path = Path(self.config.text_index_path)

        # ── Try loading from cache ──
        if (not force_rebuild
            and img_emb_path.exists() and txt_emb_path.exists()
            and img_idx_path.exists() and txt_idx_path.exists()):

            logger.info("Loading cached embeddings and indices...")
            self.image_embeddings = np.load(str(img_emb_path))
            self.text_embeddings = np.load(str(txt_emb_path))

            n_meta = len(self.metadata)
            if (self.image_embeddings.shape[0] == n_meta
                and self.text_embeddings.shape[0] == n_meta):

                actual_dim = self.text_embeddings.shape[1]
                if actual_dim != self.config.embedding_dim:
                    logger.info(
                        f"Updating embedding_dim: {self.config.embedding_dim} -> {actual_dim}"
                    )
                    self.config.embedding_dim = actual_dim

                self.dual_index = DualFAISSIndex(actual_dim, self.config)
                self.dual_index.load(str(img_idx_path), str(txt_idx_path))
                self._fit_bm25()
                self._fit_spell_corrector()
                self._is_ready = True

                n_zero_img = int(np.sum(np.all(self.image_embeddings == 0, axis=1)))
                n_zero_txt = int(np.sum(np.all(self.text_embeddings == 0, axis=1)))
                logger.info(
                    f"Engine ready (from cache). "
                    f"Zero-vectors: {n_zero_img} img, {n_zero_txt} txt"
                )
                return
            else:
                logger.warning(
                    f"Cache shape mismatch: emb={self.image_embeddings.shape[0]} "
                    f"vs metadata={n_meta}. Rebuilding..."
                )

        # ── Initialize encoder ──
        if self.encoder is None:
            self.encoder = FashionCLIPEncoder(self.config)

        n = len(self.metadata)
        dim = self.config.embedding_dim
        t_start = time.time()

        # ── Step 1: Encode product text ──
        logger.info(f"Step 1/4: Encoding {n:,} product texts...")
        texts = self.metadata['search_text'].fillna(self.metadata['name']).tolist()
        product_texts = [f"a fashion product: {t}" for t in texts]
        self.text_embeddings = self._encode_texts_with_progress(product_texts, "Text embeddings")
        logger.info(f"  Text encoding done in {time.time()-t_start:.1f}s")

        # ── Step 2: Image-proxy embeddings from text ──
        logger.info("Step 2/4: Creating image-proxy embeddings from text...")
        image_proxy_texts = []
        for i in range(n):
            row = self.metadata.iloc[i]
            name = row.get('search_text', row['name'])
            if pd.isna(name) or str(name) == 'nan':
                name = row['name']
            image_proxy_texts.append(f"a fashion product photo of {name}")
        self.image_embeddings = self._encode_texts_with_progress(image_proxy_texts, "Image proxies")

        # ── Step 3: Build FAISS ──
        logger.info("Step 3/4: Building dual FAISS index...")
        self.dual_index = DualFAISSIndex(dim, self.config)
        self.dual_index.build(self.image_embeddings, self.text_embeddings)

        # ── Step 4: BM25 + Spell Corrector ──
        logger.info("Step 4/4: Fitting BM25 lexical index + spell corrector...")
        self._fit_bm25()
        self._fit_spell_corrector()

        # ── Save to persistent storage ──
        np.save(str(img_emb_path), self.image_embeddings)
        np.save(str(txt_emb_path), self.text_embeddings)
        self.dual_index.save(str(img_idx_path), str(txt_idx_path))

        self._is_ready = True

        elapsed = time.time() - t_start
        n_zero = int(np.sum(np.all(self.text_embeddings == 0, axis=1)))
        logger.info(
            f"\n{'='*60}\n"
            f"  ENGINE READY in {elapsed:.0f}s ({elapsed/60:.1f} min)\n"
            f"  Products indexed: {n:,}\n"
            f"  Embedding dim: {dim}\n"
            f"  Zero-vector texts: {n_zero}\n"
            f"  FAISS vectors: {self.dual_index.text_index.ntotal:,}\n"
            f"{'='*60}"
        )

    def _encode_texts_with_progress(self, texts: List[str], desc: str) -> np.ndarray:
        batch_size = min(self.config.embed_batch_size * 4, 256)
        texts = [str(t) if t and str(t) != 'nan' else '' for t in texts]
        all_emb = []

        n_batches = (len(texts) + batch_size - 1) // batch_size
        for i in tqdm(range(0, len(texts), batch_size), total=n_batches, desc=desc):
            batch = texts[i:i + batch_size]
            emb = self.encoder.encode_texts(batch, batch_size=len(batch))
            all_emb.append(emb)

        return np.vstack(all_emb).astype(np.float32)

    def _fit_bm25(self):
        texts = self.metadata['search_text'].fillna(self.metadata['name']).tolist()
        self.bm25 = SimpleBM25()
        self.bm25.fit(texts)

    def _fit_spell_corrector(self):
        if self.config.enable_spell_correction:
            texts = self.metadata['search_text'].fillna(self.metadata['name']).tolist()
            self.spell_corrector.fit(texts)

    # ── Search ──

    def search(
        self, query: str,
        query_image: Optional[Image.Image] = None,
        top_n: Optional[int] = None,
        text_weight: float = 0.5,
        sort_by: str = 'relevance',
    ) -> pd.DataFrame:
        if not self._is_ready:
            raise EngineNotReadyError("Engine not ready. Call build_index() first.")
        if self.encoder is None:
            self.encoder = FashionCLIPEncoder(self.config)

        top_n = top_n or self.config.final_top_n
        t_start = time.time()

        original_query = query

        # ── Multilingual: translate if needed ──
        if self.config.enable_multilingual:
            query, detected_lang, was_translated = self.multilingual.translate_query(query)
        else:
            detected_lang, was_translated = 'en', False

        # ── Spell correction ──
        was_spell_corrected = False
        spell_suggestion = None
        if self.config.enable_spell_correction and self.spell_corrector._ready:
            corrected, was_spell_corrected = self.spell_corrector.correct_query(query)
            if was_spell_corrected:
                spell_suggestion = corrected
                query = corrected

        # Parse intent
        parsed = self.query_parser.parse(query)
        parsed.has_image = query_image is not None
        parsed.text_weight = text_weight
        parsed.original_query = original_query
        parsed.detected_language = detected_lang
        parsed.was_translated = was_translated
        parsed.was_spell_corrected = was_spell_corrected
        parsed.spell_correction_suggestion = spell_suggestion

        logger.info(
            f"Query: \"{query}\" -> "
            f"cat={parsed.category_filter}, col={parsed.color_filter}, "
            f"price=[{parsed.price_min},{parsed.price_max}], "
            f"gen={parsed.gender_filter}, tags={parsed.style_tags}, "
            f"mat={parsed.material_filter}, size={parsed.size_filter}, "
            f"excl={parsed.exclusions}"
            f"{' [translated from ' + detected_lang + ']' if was_translated else ''}"
            f"{' [spell-corrected]' if was_spell_corrected else ''}"
        )

        # Encode query
        if query_image is not None:
            query_vec = self.encoder.encode_multimodal_query(
                parsed.vibe_text, query_image, text_weight
            )
        else:
            query_vec = self.encoder.encode_query_text(parsed.vibe_text)

        # Dual-index retrieval with RRF
        candidate_indices, rrf_scores = self.dual_index.search_fused(
            query_vec[0], top_k=self.config.retrieval_top_k,
        )

        if not candidate_indices:
            logger.warning("No candidates from FAISS.")
            return pd.DataFrame()

        candidates = self.metadata.iloc[candidate_indices].copy()
        candidates['rrf_score'] = rrf_scores
        candidates['_orig_idx'] = candidate_indices

        # Metadata filter
        filtered = reranker.apply_filters(candidates, parsed)
        if len(filtered) == 0:
            logger.warning("Zero results after filtering. Relaxing constraints...")
            filtered = reranker.relax_and_retry(candidates, parsed, min_results=top_n)

        # Hybrid re-ranking
        ranked = reranker.hybrid_rerank(filtered, parsed, self.config, self.bm25)

        # Build result
        result_cols = [
            'sku', 'name', 'brand', 'price', 'color_clean', 'color_family',
            'category', 'gender', 'style_tags', 'primary_image_url', 'image_urls',
            'rrf_score', 'hybrid_score', 'any_in_stock', 'sizes_available',
            'product_details', 'materials', 'url',
        ]
        available_cols = [c for c in result_cols if c in ranked.columns]
        results = ranked[available_cols].head(top_n).reset_index(drop=True)

        # ── Apply sort ──
        if sort_by != 'relevance' and sort_by in self.SORT_OPTIONS:
            sort_col, ascending = self.SORT_OPTIONS[sort_by]
            if sort_col in results.columns:
                results = results.sort_values(sort_col, ascending=ascending).reset_index(drop=True)

        results.index = range(1, len(results) + 1)
        results.index.name = 'rank'

        # ── Generate suggested related searches ──
        suggested_searches = reranker.generate_suggestions(results, parsed)

        # Attach query metadata for frontend use
        results.attrs['query_info'] = {
            'original_query': original_query,
            'processed_query': query,
            'detected_language': detected_lang,
            'was_translated': was_translated,
            'was_spell_corrected': was_spell_corrected,
            'spell_suggestion': spell_suggestion,
            'parsed_category': parsed.category_filter,
            'parsed_color': parsed.color_filter,
            'parsed_price_range': [parsed.price_min, parsed.price_max],
            'parsed_gender': parsed.gender_filter,
            'parsed_style_tags': parsed.style_tags,
            'parsed_material': parsed.material_filter,
            'parsed_size': parsed.size_filter,
            'parsed_exclusions': parsed.exclusions,
            'sort_by': sort_by,
            'available_sorts': list(self.SORT_OPTIONS.keys()),
            'suggested_searches': suggested_searches,
        }

        elapsed = time.time() - t_start
        logger.info(
            f"Search complete: {len(results)} results in {elapsed:.2f}s "
            f"(from {len(candidates)} candidates -> {len(filtered)} filtered)"
        )
        return results

    def search_similar(self, sku, top_n: int = 10) -> pd.DataFrame:
        """Find visually similar products to a given SKU."""
        if not self._is_ready:
            raise EngineNotReadyError("Engine not ready.")

        # ── FIX: compare as strings consistently ──
        sku_str = str(sku)
        match = self.metadata[self.metadata['sku'] == sku_str]
        if len(match) == 0:
            raise SKUNotFoundError(sku_str)

        idx = match.index[0]
        query_vec = self.image_embeddings[idx]

        dists, ids = self.dual_index.search_image_index(query_vec, top_n + 1)
        ids, dists = ids[0], dists[0]
        mask = ids != idx
        ids, dists = ids[mask][:top_n], dists[mask][:top_n]

        results = self.metadata.iloc[ids].copy()
        results['similarity_score'] = dists
        return results.reset_index(drop=True)

    def search_by_image(self, image: Image.Image, top_n: int = 20) -> pd.DataFrame:
        """Search using an uploaded image only (no text query)."""
        if self.encoder is None:
            self.encoder = FashionCLIPEncoder(self.config)
        img_emb = self.encoder.encode_images([image])
        indices, scores = self.dual_index.search_fused(
            img_emb[0], top_n, image_weight=0.8, text_weight=0.2,
        )
        results = self.metadata.iloc[indices].copy()
        results['score'] = scores
        results.index = range(1, len(results) + 1)
        results.index.name = 'rank'
        return results

    def get_product_detail(self, sku) -> Optional[Dict]:
        """
        Get full product detail for a single SKU — used when a user clicks a card.
        Returns all metadata + all image URLs for the product detail page.
        """
        sku_str = str(sku)
        match = self.metadata[self.metadata['sku'] == sku_str]
        if len(match) == 0:
            return None

        row = match.iloc[0]
        detail = row.to_dict()

        # Ensure image_urls is a proper list
        if 'image_urls' in detail and isinstance(detail['image_urls'], str):
            try:
                detail['image_urls'] = ast.literal_eval(detail['image_urls'])
            except (ValueError, SyntaxError):
                detail['image_urls'] = [detail.get('primary_image_url', '')]

        return detail

    # ── "Complete the Look" — cross-category outfit recommendation ──

    def complete_the_look(self, sku, n_per_category: int = 3) -> Dict[str, pd.DataFrame]:
        """
        Given a product SKU, suggest complementary items from DIFFERENT categories
        to help the user build a complete outfit.

        v3.3 improvements:
          - Searches per-category pools (not just top-200 global neighbors)
          - Scores by style coherence (tag overlap), color harmony, price tier,
            gender consistency, and embedding similarity
          - Returns genuinely complementary items, not just same-category lookalikes

        Returns a dict mapping category names to DataFrames of recommendations.
        """
        if not self._is_ready:
            raise EngineNotReadyError("Engine not ready.")

        sku_str = str(sku)
        match = self.metadata[self.metadata['sku'] == sku_str]
        if len(match) == 0:
            raise SKUNotFoundError(sku_str)

        source = match.iloc[0]
        source_category = source.get('category', '')
        source_idx = match.index[0]
        source_color = str(source.get('color_family', '')).lower()
        source_gender = source.get('gender', '')
        source_price = source.get('price', 0)
        source_tags = source.get('style_tags', [])
        if not isinstance(source_tags, list):
            source_tags = []
        source_tag_set = set(source_tags)

        target_categories = self.OUTFIT_PAIRS.get(
            source_category, ['Shoes', 'Accessories', 'Bags']
        )

        # Get compatible colors for the source product
        compatible_colors = set(self.COLOR_HARMONY.get(source_color, []))
        compatible_colors.add(source_color)  # same color is always ok

        # Get a broad set of candidates from fused search (both indices)
        query_vec = self.image_embeddings[source_idx]
        _, img_ids = self.dual_index.search_image_index(query_vec, 800)
        _, txt_ids = self.dual_index.search_text_index(query_vec, 800)
        img_ids = set(int(i) for i in img_ids[0] if i >= 0 and i != source_idx)
        txt_ids = set(int(i) for i in txt_ids[0] if i >= 0 and i != source_idx)
        all_candidate_ids = img_ids | txt_ids

        # Price tier: items within 0.3x-3x of source price
        price_low = max(source_price * 0.3, 3.0)
        price_high = source_price * 3.0

        outfit = {}
        for target_cat in target_categories:
            # Filter candidates to this category
            cat_mask = self.metadata['category'] == target_cat
            cat_indices = set(self.metadata.index[cat_mask].tolist())
            pool = list(all_candidate_ids & cat_indices)

            if not pool:
                continue

            # Score each candidate with a multi-factor outfit coherence score
            scores = []
            for cidx in pool:
                row = self.metadata.iloc[cidx]

                # 1. Embedding similarity (0-1, already normalized)
                sim = max(0.0, float(np.dot(query_vec, self.image_embeddings[cidx])))

                # 2. Style tag overlap
                c_tags = row.get('style_tags', [])
                if isinstance(c_tags, list) and source_tag_set:
                    tag_overlap = len(set(c_tags) & source_tag_set) / max(len(source_tag_set), 1)
                else:
                    tag_overlap = 0.0

                # 3. Color harmony
                c_color = str(row.get('color_family', '')).lower()
                if c_color in compatible_colors:
                    color_score = 1.0
                elif c_color in ('black', 'white', 'grey', 'navy', 'beige'):
                    color_score = 0.7  # neutrals always work
                else:
                    color_score = 0.2

                # 4. Gender consistency (empty gender = universal match)
                c_gender = row.get('gender', '')
                if (not c_gender or not source_gender or
                        c_gender == source_gender or
                        c_gender == 'Unisex' or source_gender == 'Unisex'):
                    gender_score = 1.0
                else:
                    gender_score = 0.0

                # 5. Price tier proximity
                c_price = row.get('price', 0)
                price_range = price_high - price_low
                if price_range > 0 and price_low <= c_price <= price_high:
                    price_score = 1.0 - abs(c_price - source_price) / price_range
                else:
                    price_score = 0.1

                # 6. In-stock bonus
                stock_score = 1.0 if row.get('any_in_stock', False) else 0.3

                # Weighted combination
                outfit_score = (
                    0.30 * sim +
                    0.25 * tag_overlap +
                    0.15 * color_score +
                    0.15 * gender_score +
                    0.10 * price_score +
                    0.05 * stock_score
                )
                scores.append((cidx, outfit_score))

            # Sort by outfit coherence score and take top n
            scores.sort(key=lambda x: -x[1])
            top_items = scores[:n_per_category]

            if top_items:
                indices = [s[0] for s in top_items]
                df = self.metadata.iloc[indices].copy()
                df['outfit_score'] = [s[1] for s in top_items]
                outfit[target_cat] = df.reset_index(drop=True)

        return outfit

    # ── Audit ──

    def audit(self) -> Dict:
        """Print diagnostic report of engine state."""
        report = {"status": "ready" if self._is_ready else "not_ready"}
        if self.metadata is not None:
            n = len(self.metadata)
            report["products"] = n
            report["has_price"] = int(self.metadata['price'].notna().sum())
            report["has_image_url"] = int(
                self.metadata['primary_image_url'].apply(
                    lambda x: isinstance(x, str) and x.startswith('http')
                ).sum()
            )
            report["has_search_text"] = int(self.metadata['search_text'].notna().sum())
            if 'color_family' in self.metadata.columns:
                report["color_families"] = sorted(self.metadata['color_family'].dropna().unique().tolist())
            if 'category' in self.metadata.columns:
                report["categories"] = sorted(self.metadata['category'].dropna().unique().tolist())

        if self.text_embeddings is not None:
            report["text_embeddings"] = self.text_embeddings.shape
            report["zero_text_emb"] = int(np.sum(np.all(self.text_embeddings == 0, axis=1)))
        if self.image_embeddings is not None:
            report["image_embeddings"] = self.image_embeddings.shape
            report["zero_img_emb"] = int(np.sum(np.all(self.image_embeddings == 0, axis=1)))
        if self.dual_index and self.dual_index.image_index:
            report["faiss_image_vectors"] = self.dual_index.image_index.ntotal
            report["faiss_text_vectors"] = self.dual_index.text_index.ntotal

        report["multilingual_enabled"] = self.config.enable_multilingual
        report["spell_correction_enabled"] = self.config.enable_spell_correction
        report["spell_corrector_vocab_size"] = len(self.spell_corrector.word_freq) if self.spell_corrector._ready else 0

        print("\n" + "=" * 55)
        print("  ENGINE AUDIT")
        print("=" * 55)
        for k, v in report.items():
            print(f"  {k:30s}  {v}")
        print("=" * 55)
        return report
