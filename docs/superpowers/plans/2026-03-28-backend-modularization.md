# ASOS Backend Modularization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the 2,789-line monolithic search engine into a modular FastAPI backend with proper project structure, typed API contracts, and tests.

**Architecture:** FastAPI app with engine modules extracted from monolith. Engine singleton loaded at startup via lifespan. Routers delegate to a service layer that bridges Pydantic models and engine DataFrames. All product data in-memory from CSV.

**Tech Stack:** Python 3.10+, FastAPI, Uvicorn, Pydantic v2, pydantic-settings, FashionCLIP (transformers), FAISS, PyTorch, NumPy, Pandas, pytest, python-multipart

---

## File Map

All paths relative to `Asos_Engine_Project/`.

**Create:**
- `backend/app/__init__.py`
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/exceptions.py`
- `backend/app/dependencies.py`
- `backend/app/models/__init__.py`
- `backend/app/models/search.py`
- `backend/app/models/product.py`
- `backend/app/routers/__init__.py`
- `backend/app/routers/health.py`
- `backend/app/routers/search.py`
- `backend/app/routers/products.py`
- `backend/app/engine/__init__.py`
- `backend/app/engine/nlp.py`
- `backend/app/engine/query_parser.py`
- `backend/app/engine/bm25.py`
- `backend/app/engine/encoder.py`
- `backend/app/engine/index.py`
- `backend/app/engine/reranker.py`
- `backend/app/engine/search_engine.py`
- `backend/app/engine/evaluator.py`
- `backend/app/services/__init__.py`
- `backend/app/services/search_service.py`
- `backend/tests/__init__.py`
- `backend/tests/conftest.py`
- `backend/tests/test_query_parser.py`
- `backend/tests/test_nlp.py`
- `backend/tests/test_bm25.py`
- `backend/tests/test_api_health.py`
- `backend/tests/test_api_search.py`
- `backend/tests/test_api_products.py`
- `backend/requirements.txt`
- `backend/pyproject.toml`
- `documentation/CLAUDE.md`
- `documentation/techstack.md`
- `documentation/prd.md`
- `documentation/progress.md`
- `documentation/plan.md`
- `documentation/architecture.md`
- `documentation/flow.md`
- `README.md`

**Source (read-only reference):**
- `finalized_search_engine_full_script.py` (monolith — lines referenced per task)

---

## Phase 1: Project Scaffolding

### Task 1: Create project structure and config

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: all other `__init__.py` files

- [ ] **Step 1: Create directory structure**

```bash
cd "Asos_Engine_Project"
mkdir -p backend/app/models backend/app/routers backend/app/engine backend/app/services backend/tests
```

- [ ] **Step 2: Create pyproject.toml**

```toml
[project]
name = "asos-search-backend"
version = "1.0.0"
description = "ASOS Multimodal Fashion Search Engine API"
requires-python = ">=3.10"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 3: Create requirements.txt**

```
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
pydantic>=2.0
pydantic-settings>=2.0
python-multipart>=0.0.6
numpy>=1.24.0
pandas>=2.0.0
torch>=2.0.0
transformers>=4.30.0
faiss-cpu>=1.7.4
Pillow>=10.0.0
tqdm>=4.65.0
pytest>=7.0.0
httpx>=0.24.0
```

- [ ] **Step 4: Create all __init__.py files**

All empty except `backend/app/__init__.py`:

```python
"""ASOS Multimodal Fashion Search Engine Backend."""
```

Create empty `__init__.py` in: `backend/app/models/`, `backend/app/routers/`, `backend/app/engine/`, `backend/app/services/`, `backend/tests/`.

- [ ] **Step 5: Create backend/app/config.py**

Extract `SearchConfig` from monolith lines 370-476. Add `Settings` class for server config.

```python
import os
import sys
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Tuple

import torch
from pydantic_settings import BaseSettings

logger = logging.getLogger("asos_search")


def _detect_environment() -> str:
    if "google.colab" in sys.modules:
        return "colab"
    if "KAGGLE_KERNEL_RUN_TYPE" in os.environ:
        return "kaggle"
    return "local"


class Settings(BaseSettings):
    """Server-level settings loaded from environment variables."""

    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["*"]
    data_dir: str = ""
    data_path: str = ""
    persistent_dir: str = ""
    image_cache_dir: str = ""
    log_level: str = "INFO"
    hf_token: Optional[str] = None

    model_config = {"env_prefix": "ASOS_"}


@dataclass
class SearchConfig:
    """Central configuration for the search engine."""

    # Model
    primary_model: str = "patrickjohncyh/fashion-clip"
    fallback_model: str = "openai/clip-vit-base-patch32"
    embedding_dim: int = 512
    device: str = ""
    hf_token: Optional[str] = None

    # FAISS Index
    n_clusters: int = 256
    n_probe: int = 20

    # Search Pipeline
    retrieval_top_k: int = 300
    final_top_n: int = 20

    # Dual-Index Fusion
    rrf_k: int = 60
    image_index_weight: float = 0.55
    text_index_weight: float = 0.45

    # Re-ranking Weights
    alpha_clip: float = 0.55
    beta_tags: float = 0.25
    gamma_text: float = 0.15
    delta_freshness: float = 0.05

    # CLIP Prompt Ensembling
    prompt_templates: Tuple[str, ...] = (
        "a photo of {}, a fashion product",
        "a product photo of {}",
        "a fashion item: {}",
        "{}, studio product photography",
        "an e-commerce photo of {}",
    )

    # Embedding Computation
    embed_batch_size: int = 32
    embed_checkpoint_interval: int = 2000

    # Features
    enable_multilingual: bool = True
    enable_spell_correction: bool = True

    # Paths (auto-detected)
    data_dir: str = ""
    data_path: str = ""
    persistent_dir: str = ""
    image_cache_dir: str = ""

    # Derived Paths
    image_index_path: str = ""
    text_index_path: str = ""
    image_embeddings_path: str = ""
    text_embeddings_path: str = ""

    def __post_init__(self):
        if not self.device:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        if not self.hf_token:
            self.hf_token = os.environ.get("HF_TOKEN", None)

        env = _detect_environment()

        if env == "colab":
            drive_base = "/content/drive/MyDrive/Colab Notebooks"
            if not self.data_dir:
                self.data_dir = drive_base
            if not self.persistent_dir:
                self.persistent_dir = os.path.join(drive_base, "asos_engine")
            if not self.image_cache_dir:
                self.image_cache_dir = "/content/asos_image_cache"
        elif env == "kaggle":
            if not self.data_dir:
                self.data_dir = "/kaggle/input"
            if not self.persistent_dir:
                self.persistent_dir = "/kaggle/working/asos_engine"
            if not self.image_cache_dir:
                self.image_cache_dir = "/kaggle/working/asos_image_cache"
        else:
            # Local / server: resolve relative to project root
            project_root = str(Path(__file__).resolve().parent.parent.parent)
            if not self.data_dir:
                self.data_dir = project_root
            if not self.persistent_dir:
                self.persistent_dir = os.path.join(project_root, "asos_engine")
            if not self.image_cache_dir:
                self.image_cache_dir = os.path.join(project_root, "asos_image_cache")

        if not self.data_path:
            pq = Path(self.data_dir) / "asos_clean.parquet"
            csv = Path(self.data_dir) / "asos_clean.csv"
            if pq.exists():
                self.data_path = str(pq)
            elif csv.exists():
                self.data_path = str(csv)
            else:
                self.data_path = str(csv)

        Path(self.persistent_dir).mkdir(parents=True, exist_ok=True)

        p = Path(self.persistent_dir)
        self.image_index_path = str(p / "faiss_image_index.bin")
        self.text_index_path = str(p / "faiss_text_index.bin")
        self.image_embeddings_path = str(p / "image_embeddings.npy")
        self.text_embeddings_path = str(p / "text_embeddings.npy")

    @classmethod
    def from_settings(cls, settings: Settings) -> "SearchConfig":
        """Create SearchConfig from server Settings, allowing env overrides."""
        kwargs = {}
        if settings.data_dir:
            kwargs["data_dir"] = settings.data_dir
        if settings.data_path:
            kwargs["data_path"] = settings.data_path
        if settings.persistent_dir:
            kwargs["persistent_dir"] = settings.persistent_dir
        if settings.image_cache_dir:
            kwargs["image_cache_dir"] = settings.image_cache_dir
        if settings.hf_token:
            kwargs["hf_token"] = settings.hf_token
        return cls(**kwargs)
```

- [ ] **Step 6: Commit**

```bash
git add backend/
git commit -m "feat: scaffold project structure with config and dependencies"
```

---

## Phase 2: Engine Modules

### Task 2: engine/nlp.py — MultilingualHandler + SpellCorrector

**Files:**
- Create: `backend/app/engine/nlp.py`

- [ ] **Step 1: Create nlp.py**

Extract `MultilingualHandler` (monolith lines 80-247) and `SpellCorrector` (monolith lines 253-364) into `backend/app/engine/nlp.py`. Keep all code identical except:
- Add proper module imports at top
- Add `__all__` export

The file should contain exactly:
- All imports needed (re, logging, typing, collections.Counter)
- `MultilingualHandler` class with FASHION_DICT, script detection regexes, detect_language(), translate_query()
- `SpellCorrector` class with fit(), _edits1(), _edits2(), _known(), correct_word(), correct_query()

- [ ] **Step 2: Commit**

```bash
git add backend/app/engine/nlp.py
git commit -m "feat: extract MultilingualHandler and SpellCorrector into engine/nlp.py"
```

### Task 3: engine/query_parser.py — ParsedQuery + QueryParser

**Files:**
- Create: `backend/app/engine/query_parser.py`

- [ ] **Step 1: Create query_parser.py**

Extract `ParsedQuery` dataclass (monolith lines 776-802) and `QueryParser` class (monolith lines 805-1056) into `backend/app/engine/query_parser.py`.

Keep all code identical. Imports needed: re, logging, dataclasses, typing.

- [ ] **Step 2: Commit**

```bash
git add backend/app/engine/query_parser.py
git commit -m "feat: extract ParsedQuery and QueryParser into engine/query_parser.py"
```

### Task 4: engine/bm25.py — SimpleBM25

**Files:**
- Create: `backend/app/engine/bm25.py`

- [ ] **Step 1: Create bm25.py**

Extract `SimpleBM25` (monolith lines 1062-1102). Imports: re, typing, collections.Counter, numpy.

- [ ] **Step 2: Commit**

```bash
git add backend/app/engine/bm25.py
git commit -m "feat: extract SimpleBM25 into engine/bm25.py"
```

### Task 5: engine/encoder.py — FashionCLIPEncoder

**Files:**
- Create: `backend/app/engine/encoder.py`

- [ ] **Step 1: Create encoder.py**

Extract `FashionCLIPEncoder` (monolith lines 482-652). Imports: logging, typing, pathlib.Path, numpy, torch, torch.nn.functional, PIL.Image, transformers (CLIPModel, CLIPProcessor).

Import `SearchConfig` from `backend.app.config`.

- [ ] **Step 2: Commit**

```bash
git add backend/app/engine/encoder.py
git commit -m "feat: extract FashionCLIPEncoder into engine/encoder.py"
```

### Task 6: engine/index.py — DualFAISSIndex

**Files:**
- Create: `backend/app/engine/index.py`

- [ ] **Step 1: Create index.py**

Extract `DualFAISSIndex` (monolith lines 658-770). Imports: logging, typing, numpy, faiss.

Import `SearchConfig` from `backend.app.config`.

- [ ] **Step 2: Commit**

```bash
git add backend/app/engine/index.py
git commit -m "feat: extract DualFAISSIndex into engine/index.py"
```

### Task 7: engine/reranker.py — Filtering + Relaxation + Reranking

**Files:**
- Create: `backend/app/engine/reranker.py`

- [ ] **Step 1: Create reranker.py**

Extract these methods from `ASOSSearchEngine` into standalone functions:

```python
import logging
from collections import Counter
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from backend.app.config import SearchConfig
from backend.app.engine.query_parser import ParsedQuery
from backend.app.engine.bm25 import SimpleBM25

logger = logging.getLogger("asos_search")


def apply_filters(candidates: pd.DataFrame, parsed: ParsedQuery) -> pd.DataFrame:
    """Apply metadata filters to candidate products."""
    # Exact code from monolith _apply_filters (lines 1817-1879)
    df = candidates
    if parsed.category_filter and "category" in df.columns:
        df = df[df["category"] == parsed.category_filter]
    if parsed.color_filter and "color_family" in df.columns:
        df = df[df["color_family"].str.lower() == parsed.color_filter.lower()]
    if parsed.gender_filter and "gender" in df.columns:
        df = df[(df["gender"] == parsed.gender_filter) | (df["gender"] == "Unisex")]
    if parsed.price_min is not None and "price" in df.columns:
        df = df[df["price"] >= parsed.price_min]
    if parsed.price_max is not None and "price" in df.columns:
        df = df[df["price"] <= parsed.price_max]
    if parsed.brand_filter and "brand" in df.columns:
        df = df[df["brand"].str.lower() == parsed.brand_filter.lower()]

    if parsed.size_filter and "sizes_available" in df.columns:
        size_val = parsed.size_filter.lower().strip()
        df = df[df["sizes_available"].apply(
            lambda sizes: any(
                size_val == str(s).lower().strip()
                for s in (sizes if isinstance(sizes, list) else [])
            ) if isinstance(sizes, list) else False
        )]

    if parsed.material_filter and "materials" in df.columns:
        mat = parsed.material_filter.lower()
        df = df[df["materials"].apply(
            lambda mats: (
                any(mat in str(m).lower() for m in mats)
                if isinstance(mats, list) and len(mats) > 0
                else mat in str(mats).lower() if mats else False
            )
        )]

    if parsed.exclusions:
        for excl in parsed.exclusions:
            excl_lower = excl.lower()
            mask = pd.Series(True, index=df.index)
            if "name" in df.columns:
                mask &= ~df["name"].str.lower().str.contains(excl_lower, na=False)
            if "color_clean" in df.columns:
                mask &= ~df["color_clean"].str.lower().str.contains(excl_lower, na=False)
            if "color_family" in df.columns:
                mask &= ~(df["color_family"].str.lower() == excl_lower)
            if "style_tags" in df.columns:
                mask &= ~df["style_tags"].apply(
                    lambda tags: any(excl_lower in str(t).lower() for t in tags)
                    if isinstance(tags, list) else False
                )
            if "materials" in df.columns:
                mask &= ~df["materials"].apply(
                    lambda mats: any(excl_lower in str(m).lower()
                                     for m in (mats if isinstance(mats, list) else []))
                )
            df = df[mask]

    if parsed.in_stock_only and "any_in_stock" in df.columns:
        df = df[df["any_in_stock"] == True]
    return df


def relax_and_retry(
    candidates: pd.DataFrame, parsed: ParsedQuery, min_results: int = 10
) -> pd.DataFrame:
    """Progressive filter relaxation — never returns empty results."""
    # Exact code from monolith _relax_and_retry (lines 1881-1991)
    relaxed = ParsedQuery(
        raw_query=parsed.raw_query, vibe_text=parsed.vibe_text,
        category_filter=parsed.category_filter, color_filter=parsed.color_filter,
        gender_filter=parsed.gender_filter, price_min=parsed.price_min,
        price_max=parsed.price_max, brand_filter=parsed.brand_filter,
        in_stock_only=parsed.in_stock_only, style_tags=parsed.style_tags,
        material_filter=parsed.material_filter, size_filter=parsed.size_filter,
        exclusions=parsed.exclusions,
    )

    best_so_far = pd.DataFrame()

    for attr in ("size_filter", "material_filter"):
        if getattr(relaxed, attr) is not None:
            saved = getattr(relaxed, attr)
            setattr(relaxed, attr, None)
            result = apply_filters(candidates, relaxed)
            if len(result) >= min_results:
                logger.info(f"Relaxed filter '{attr}' -> {len(result)} results")
                return result
            if len(result) > len(best_so_far):
                best_so_far = result
            else:
                setattr(relaxed, attr, saved)

    if relaxed.exclusions:
        relaxed.exclusions = []
        result = apply_filters(candidates, relaxed)
        if len(result) > len(best_so_far):
            best_so_far = result
        if len(result) >= min_results:
            logger.info(f"Relaxed exclusions -> {len(result)} results")
            return result

    non_price_relaxations = [
        ("color_filter", None), ("gender_filter", None), ("in_stock_only", False),
    ]
    for attr, val in non_price_relaxations:
        if getattr(relaxed, attr) is not None and getattr(relaxed, attr) != val:
            setattr(relaxed, attr, val)
            result = apply_filters(candidates, relaxed)
            if len(result) > len(best_so_far):
                best_so_far = result
            if len(result) >= min_results:
                logger.info(f"Relaxed filter '{attr}' -> {len(result)} results")
                return result

    if parsed.price_max is not None:
        original_max = parsed.price_max
        for factor in [1.5, 2.0, 3.0, 5.0, 10.0]:
            relaxed.price_max = original_max * factor
            result = apply_filters(candidates, relaxed)
            if len(result) > len(best_so_far):
                best_so_far = result
            if len(result) >= min_results:
                logger.info(
                    f"Expanded price_max: £{original_max:.0f} -> "
                    f"£{relaxed.price_max:.0f} ({factor}x) -> {len(result)} results"
                )
                return result
        relaxed.price_max = None
        result = apply_filters(candidates, relaxed)
        if len(result) > len(best_so_far):
            best_so_far = result
        if len(result) >= min_results:
            logger.info(f"Dropped price_max entirely -> {len(result)} results")
            return result

    if parsed.price_min is not None:
        relaxed.price_min = None
        result = apply_filters(candidates, relaxed)
        if len(result) > len(best_so_far):
            best_so_far = result
        if len(result) >= min_results:
            logger.info(f"Dropped price_min -> {len(result)} results")
            return result

    if relaxed.category_filter is not None:
        relaxed.category_filter = None
        result = apply_filters(candidates, relaxed)
        if len(result) > len(best_so_far):
            best_so_far = result
        if len(result) >= min_results:
            logger.info(f"Relaxed category_filter -> {len(result)} results")
            return result

    if len(best_so_far) > 0:
        logger.info(f"Returning best available: {len(best_so_far)} results (wanted {min_results})")
        return best_so_far

    logger.warning("All filters relaxed. Returning unfiltered results.")
    return candidates


def hybrid_rerank(
    candidates: pd.DataFrame, parsed: ParsedQuery, config: SearchConfig,
    bm25: Optional[SimpleBM25] = None,
) -> pd.DataFrame:
    """Hybrid re-ranking with RRF, tag overlap, BM25, and bonuses."""
    # Exact code from monolith _hybrid_rerank (lines 1995-2086)
    scored = candidates.copy()
    if len(scored) == 0:
        return scored

    rrf_vals = scored["rrf_score"].values
    rrf_min, rrf_max = rrf_vals.min(), rrf_vals.max()
    scored["rrf_norm"] = (
        (rrf_vals - rrf_min) / (rrf_max - rrf_min) if rrf_max > rrf_min else 1.0
    )

    query_tags = set(parsed.style_tags)
    if query_tags and "style_tags" in scored.columns:
        scored["tag_score"] = scored["style_tags"].apply(
            lambda tags: (
                len(set(tags) & query_tags) / len(query_tags)
                if isinstance(tags, list) and query_tags else 0.0
            )
        )
    else:
        scored["tag_score"] = 0.0

    if bm25 is not None and "_orig_idx" in scored.columns:
        bm25_raw = bm25.score_candidates(parsed.raw_query, scored["_orig_idx"].tolist())
        bm25_max = bm25_raw.max()
        scored["bm25_norm"] = bm25_raw / bm25_max if bm25_max > 0 else 0.0
    else:
        scored["bm25_norm"] = 0.0

    if "any_in_stock" in scored.columns:
        scored["stock_bonus"] = scored["any_in_stock"].astype(float)
    else:
        scored["stock_bonus"] = 0.5

    mat_bonus = np.zeros(len(scored), dtype=np.float32)
    if parsed.material_filter and "materials" in scored.columns:
        mat_q = parsed.material_filter.lower()
        mat_bonus = scored["materials"].apply(
            lambda mats: 1.0 if isinstance(mats, list) and any(
                mat_q in str(m).lower() for m in mats
            ) else 0.0
        ).values.astype(np.float32)
    scored["material_bonus"] = mat_bonus

    price_proximity = np.zeros(len(scored), dtype=np.float32)
    target_price = parsed.price_max or parsed.price_min
    if target_price is not None and "price" in scored.columns:
        prices = scored["price"].values.astype(np.float32)
        sigma = max(target_price * 0.5, 10.0)
        price_proximity = np.exp(-((prices - target_price) ** 2) / (2 * sigma ** 2))
    scored["price_proximity"] = price_proximity

    has_price_intent = target_price is not None
    has_material_intent = parsed.material_filter is not None

    if has_price_intent:
        scored["hybrid_score"] = (
            0.40 * scored["rrf_norm"] +
            0.18 * scored["tag_score"] +
            0.10 * scored["bm25_norm"] +
            0.05 * scored["stock_bonus"] +
            0.20 * scored["price_proximity"] +
            0.07 * scored["material_bonus"]
        )
    elif has_material_intent:
        scored["hybrid_score"] = (
            0.45 * scored["rrf_norm"] +
            0.20 * scored["tag_score"] +
            0.12 * scored["bm25_norm"] +
            0.05 * scored["stock_bonus"] +
            0.18 * scored["material_bonus"]
        )
    else:
        scored["hybrid_score"] = (
            config.alpha_clip * scored["rrf_norm"] +
            config.beta_tags * scored["tag_score"] +
            config.gamma_text * scored["bm25_norm"] +
            config.delta_freshness * scored["stock_bonus"]
        )
    return scored.sort_values("hybrid_score", ascending=False)


def generate_suggestions(
    results: pd.DataFrame, parsed: ParsedQuery, max_suggestions: int = 5
) -> List[str]:
    """Generate related search suggestions."""
    # Exact code from monolith _generate_suggestions (lines 1679-1771)
    if len(results) == 0:
        return []

    suggestions = []
    cat = parsed.category_filter
    cat_names = {
        "Dresses": "dresses", "Tops": "tops", "Coats & Jackets": "jackets",
        "Knitwear": "knitwear", "Jeans": "jeans", "Trousers": "trousers",
        "Shoes": "shoes", "Bags": "bags", "Accessories": "accessories",
        "Skirts": "skirts", "Shorts": "shorts", "Swimwear": "swimwear",
        "Hoodies & Sweatshirts": "hoodies", "Suits & Tailoring": "suits",
        "Jumpsuits & Playsuits": "jumpsuits",
    }
    base_term = cat_names.get(cat, parsed.vibe_text.strip()[:30]) if cat in cat_names else parsed.vibe_text.strip()[:30]

    if "color_family" in results.columns and not parsed.color_filter:
        top_colors = results["color_family"].value_counts().head(4).index.tolist()
        for color in top_colors[:2]:
            if color and color not in ("other", "multi"):
                suggestions.append(f"{color} {base_term}")

    if parsed.color_filter and "color_family" in results.columns:
        for ac in ["black", "white", "navy", "beige"]:
            if ac != parsed.color_filter:
                suggestions.append(f"{ac} {base_term}")
                break

    if parsed.price_max is None and parsed.price_min is None and "price" in results.columns:
        p25 = results["price"].quantile(0.25)
        if p25 > 5:
            suggestions.append(f"{base_term} under \u00a3{int(p25)}")

    if "style_tags" in results.columns:
        tag_counts = Counter()
        for tags in results["style_tags"]:
            if isinstance(tags, list):
                for t in tags:
                    if t not in parsed.style_tags and t not in parsed.vibe_text:
                        tag_counts[t] += 1
        if tag_counts:
            suggestions.append(f"{tag_counts.most_common(1)[0][0]} {base_term}")

    if "brand" in results.columns:
        top_brand = results["brand"].value_counts().head(1).index.tolist()
        if top_brand and top_brand[0] and top_brand[0] != "Unknown":
            brand = top_brand[0]
            if brand.lower() not in parsed.vibe_text.lower():
                suggestions.append(f"{brand} {base_term}")

    if cat:
        related = {
            "Dresses": "jumpsuits", "Tops": "blouses", "Jeans": "trousers",
            "Trousers": "jeans", "Coats & Jackets": "blazers", "Knitwear": "cardigans",
            "Skirts": "dresses", "Shorts": "skirts",
        }
        alt = related.get(cat)
        if alt:
            prefix = f"{parsed.color_filter} " if parsed.color_filter else ""
            suggestions.append(f"{prefix}{alt}".strip())

    seen = set()
    unique = []
    for s in suggestions:
        s_clean = s.strip().lower()
        if s_clean not in seen and s_clean != parsed.raw_query.lower():
            seen.add(s_clean)
            unique.append(s.strip())
    return unique[:max_suggestions]
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/engine/reranker.py
git commit -m "feat: extract filtering, relaxation, and reranking into engine/reranker.py"
```

### Task 8: engine/search_engine.py — Refactored ASOSSearchEngine

**Files:**
- Create: `backend/app/engine/search_engine.py`

- [ ] **Step 1: Create search_engine.py**

Refactored orchestrator that delegates to the extracted modules. Contains:
- `ASOSSearchEngine.__init__()`, `load_data()`, `build_index()` — same as monolith
- `search()` — delegates filtering to `reranker.apply_filters`, reranking to `reranker.hybrid_rerank`
- `search_similar()`, `search_by_image()`, `get_product_detail()` — same as monolith
- `complete_the_look()` — same as monolith (with OUTFIT_PAIRS, COLOR_HARMONY, SORT_OPTIONS as class attrs)
- `audit()` — same as monolith
- `_encode_texts_with_progress()`, `_fit_bm25()`, `_fit_spell_corrector()` — same as monolith

Key imports:
```python
from backend.app.config import SearchConfig
from backend.app.engine.encoder import FashionCLIPEncoder
from backend.app.engine.index import DualFAISSIndex
from backend.app.engine.query_parser import QueryParser, ParsedQuery
from backend.app.engine.bm25 import SimpleBM25
from backend.app.engine.nlp import MultilingualHandler, SpellCorrector
from backend.app.engine import reranker
```

The `search()` method replaces `self._apply_filters(...)` with `reranker.apply_filters(...)`, `self._relax_and_retry(...)` with `reranker.relax_and_retry(...)`, `self._hybrid_rerank(...)` with `reranker.hybrid_rerank(..., self.config, self.bm25)`, and `self._generate_suggestions(...)` with `reranker.generate_suggestions(...)`.

- [ ] **Step 2: Commit**

```bash
git add backend/app/engine/search_engine.py
git commit -m "feat: refactored ASOSSearchEngine delegating to extracted modules"
```

### Task 9: engine/evaluator.py — SearchEvaluator + EvalResult

**Files:**
- Create: `backend/app/engine/evaluator.py`

- [ ] **Step 1: Create evaluator.py**

Extract `EvalResult` dataclass and `SearchEvaluator` class (monolith lines 2092-2172). Keep identical. Import `ASOSSearchEngine` with TYPE_CHECKING to avoid circular imports.

- [ ] **Step 2: Update engine/__init__.py with exports**

```python
"""ASOS Search Engine core modules."""

from backend.app.engine.search_engine import ASOSSearchEngine
from backend.app.engine.evaluator import SearchEvaluator

__all__ = ["ASOSSearchEngine", "SearchEvaluator"]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/engine/
git commit -m "feat: extract SearchEvaluator and set up engine package exports"
```

---

## Phase 3: FastAPI Layer

### Task 10: exceptions.py + dependencies.py

**Files:**
- Create: `backend/app/exceptions.py`
- Create: `backend/app/dependencies.py`

- [ ] **Step 1: Create exceptions.py**

```python
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
```

- [ ] **Step 2: Create dependencies.py**

```python
from fastapi import Request

from backend.app.engine.search_engine import ASOSSearchEngine
from backend.app.exceptions import EngineNotReadyError


def get_engine(request: Request) -> ASOSSearchEngine:
    """FastAPI dependency: retrieve the engine singleton from app state."""
    engine: ASOSSearchEngine = getattr(request.app.state, "engine", None)
    if engine is None or not engine._is_ready:
        raise EngineNotReadyError("Search engine is not ready")
    return engine
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/exceptions.py backend/app/dependencies.py
git commit -m "feat: add custom exceptions and FastAPI dependency injection"
```

### Task 11: Pydantic models

**Files:**
- Create: `backend/app/models/search.py`
- Create: `backend/app/models/product.py`

- [ ] **Step 1: Create models/search.py**

```python
from typing import Optional
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Search query text")
    top_n: int = Field(20, ge=1, le=100, description="Number of results to return")
    sort_by: str = Field("relevance", description="Sort order: relevance, price_asc, price_desc, name_asc, name_desc")
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


class SimilarRequest(BaseModel):
    top_n: int = Field(10, ge=1, le=100)


class EvaluateRequest(BaseModel):
    test_queries: list[dict]
    k_values: list[int] = [5, 10, 20]
```

- [ ] **Step 2: Create models/product.py**

```python
from typing import Any, Optional
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
```

- [ ] **Step 3: Update models/__init__.py**

```python
from backend.app.models.search import (
    SearchRequest, SearchResponse, SearchResultItem, QueryInfo,
    ImageSearchRequest, EvaluateRequest,
)
from backend.app.models.product import (
    ProductDetail, OutfitResponse, OutfitItem,
    SimilarProductItem, SimilarResponse,
)
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add Pydantic request/response models for search and product APIs"
```

### Task 12: services/search_service.py

**Files:**
- Create: `backend/app/services/search_service.py`

- [ ] **Step 1: Create search_service.py**

```python
import base64
import io
import logging
from typing import Optional

import pandas as pd
from PIL import Image

from backend.app.engine.search_engine import ASOSSearchEngine
from backend.app.exceptions import SKUNotFoundError, InvalidQueryError
from backend.app.models.search import (
    SearchRequest, SearchResponse, SearchResultItem, QueryInfo,
)
from backend.app.models.product import (
    ProductDetail, OutfitResponse, OutfitItem,
    SimilarProductItem, SimilarResponse,
)

logger = logging.getLogger("asos_search")


def decode_image(image_b64: Optional[str] = None, image_bytes: Optional[bytes] = None) -> Optional[Image.Image]:
    """Decode a base64 string or raw bytes into a PIL Image."""
    if image_b64:
        try:
            data = base64.b64decode(image_b64)
            return Image.open(io.BytesIO(data)).convert("RGB")
        except Exception as e:
            raise InvalidQueryError(f"Invalid base64 image: {e}")
    if image_bytes:
        try:
            return Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            raise InvalidQueryError(f"Invalid image data: {e}")
    return None


def _row_to_search_item(row: pd.Series) -> SearchResultItem:
    """Convert a DataFrame row to a SearchResultItem."""
    return SearchResultItem(
        sku=str(row.get("sku", "")),
        name=str(row.get("name", "")),
        brand=str(row.get("brand", "")),
        price=float(row.get("price", 0)),
        color=str(row.get("color_clean", "")),
        color_family=str(row.get("color_family", "")),
        category=str(row.get("category", "")),
        gender=str(row.get("gender", "")),
        image_url=str(row.get("primary_image_url", "")),
        score=float(row.get("hybrid_score", row.get("rrf_score", row.get("score", 0)))),
        style_tags=row.get("style_tags", []) if isinstance(row.get("style_tags"), list) else [],
        in_stock=bool(row.get("any_in_stock", True)),
    )


def _row_to_product_detail(detail: dict) -> ProductDetail:
    """Convert a product detail dict to a ProductDetail model."""
    image_urls = detail.get("image_urls", [])
    if not isinstance(image_urls, list):
        image_urls = [detail.get("primary_image_url", "")]

    return ProductDetail(
        sku=str(detail.get("sku", "")),
        name=str(detail.get("name", "")),
        brand=str(detail.get("brand", "")),
        price=float(detail.get("price", 0)),
        color=str(detail.get("color_clean", "")),
        color_family=str(detail.get("color_family", "")),
        category=str(detail.get("category", "")),
        gender=str(detail.get("gender", "")),
        image_url=str(detail.get("primary_image_url", "")),
        image_urls=image_urls,
        style_tags=detail.get("style_tags", []) if isinstance(detail.get("style_tags"), list) else [],
        materials=detail.get("materials", []) if isinstance(detail.get("materials"), list) else [],
        sizes_available=[str(s) for s in detail.get("sizes_available", [])] if isinstance(detail.get("sizes_available"), list) else [],
        product_details=str(detail.get("product_details", "")),
        in_stock=bool(detail.get("any_in_stock", True)),
    )


def search(engine: ASOSSearchEngine, request: SearchRequest) -> SearchResponse:
    """Execute a text (or multimodal) search and return typed response."""
    image = decode_image(image_b64=request.image_b64)

    results_df = engine.search(
        query=request.query,
        query_image=image,
        top_n=request.top_n,
        text_weight=request.text_weight,
        sort_by=request.sort_by,
    )

    items = [_row_to_search_item(row) for _, row in results_df.iterrows()]
    qi = results_df.attrs.get("query_info", {})

    query_info = QueryInfo(
        original_query=qi.get("original_query", request.query),
        processed_query=qi.get("processed_query", request.query),
        detected_language=qi.get("detected_language", "en"),
        was_translated=qi.get("was_translated", False),
        was_spell_corrected=qi.get("was_spell_corrected", False),
        spell_suggestion=qi.get("spell_suggestion"),
        parsed_category=qi.get("parsed_category"),
        parsed_color=qi.get("parsed_color"),
        parsed_price_range=qi.get("parsed_price_range", [None, None]),
        parsed_gender=qi.get("parsed_gender"),
        parsed_style_tags=qi.get("parsed_style_tags", []),
        parsed_material=qi.get("parsed_material"),
        parsed_size=qi.get("parsed_size"),
        parsed_exclusions=qi.get("parsed_exclusions", []),
        sort_by=qi.get("sort_by", "relevance"),
        available_sorts=qi.get("available_sorts", []),
        suggested_searches=qi.get("suggested_searches", []),
    )

    return SearchResponse(results=items, query_info=query_info, total=len(items))


def search_by_image(engine: ASOSSearchEngine, image: Image.Image, top_n: int = 20) -> SearchResponse:
    """Execute an image-only search."""
    results_df = engine.search_by_image(image, top_n=top_n)
    items = [_row_to_search_item(row) for _, row in results_df.iterrows()]
    query_info = QueryInfo(original_query="[image search]", processed_query="[image search]")
    return SearchResponse(results=items, query_info=query_info, total=len(items))


def get_product_detail(engine: ASOSSearchEngine, sku: str) -> ProductDetail:
    """Get full product details for a SKU."""
    detail = engine.get_product_detail(sku)
    if detail is None:
        raise SKUNotFoundError(sku)
    return _row_to_product_detail(detail)


def get_similar(engine: ASOSSearchEngine, sku: str, top_n: int = 10) -> SimilarResponse:
    """Get similar products for a SKU."""
    source_detail = engine.get_product_detail(sku)
    if source_detail is None:
        raise SKUNotFoundError(sku)

    similar_df = engine.search_similar(sku, top_n=top_n)
    items = [
        SimilarProductItem(
            sku=str(row.get("sku", "")),
            name=str(row.get("name", "")),
            brand=str(row.get("brand", "")),
            price=float(row.get("price", 0)),
            color=str(row.get("color_clean", "")),
            category=str(row.get("category", "")),
            image_url=str(row.get("primary_image_url", "")),
            similarity_score=float(row.get("similarity_score", 0)),
        )
        for _, row in similar_df.iterrows()
    ]
    return SimilarResponse(
        source=_row_to_product_detail(source_detail),
        results=items,
        total=len(items),
    )


def get_outfit(engine: ASOSSearchEngine, sku: str, n_per_category: int = 3) -> OutfitResponse:
    """Get 'Complete the Look' outfit recommendations."""
    source_detail = engine.get_product_detail(sku)
    if source_detail is None:
        raise SKUNotFoundError(sku)

    outfit_dict = engine.complete_the_look(sku, n_per_category=n_per_category)
    outfit = {}
    for cat, items_df in outfit_dict.items():
        outfit[cat] = [
            OutfitItem(
                sku=str(row.get("sku", "")),
                name=str(row.get("name", "")),
                brand=str(row.get("brand", "")),
                price=float(row.get("price", 0)),
                color_family=str(row.get("color_family", "")),
                category=str(row.get("category", "")),
                image_url=str(row.get("primary_image_url", "")),
                outfit_score=float(row.get("outfit_score", 0)),
            )
            for _, row in items_df.iterrows()
        ]

    return OutfitResponse(
        source=_row_to_product_detail(source_detail),
        outfit=outfit,
    )
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/
git commit -m "feat: add search service layer bridging FastAPI and engine"
```

### Task 13: routers/health.py

**Files:**
- Create: `backend/app/routers/health.py`

- [ ] **Step 1: Create health.py**

```python
from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    products: int
    engine_ready: bool


@router.get("/health", response_model=HealthResponse)
def health_check(request: Request) -> HealthResponse:
    engine = getattr(request.app.state, "engine", None)
    if engine is None or not engine._is_ready:
        return HealthResponse(status="loading", products=0, engine_ready=False)
    return HealthResponse(
        status="ok",
        products=len(engine.metadata),
        engine_ready=True,
    )


@router.get("/audit")
def audit(request: Request) -> dict:
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        return {"status": "engine_not_loaded"}
    return engine.audit()
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/routers/health.py
git commit -m "feat: add health check and audit endpoints"
```

### Task 14: routers/search.py

**Files:**
- Create: `backend/app/routers/search.py`

- [ ] **Step 1: Create search.py**

```python
import logging

from fastapi import APIRouter, Depends, File, Query, UploadFile

from backend.app.dependencies import get_engine
from backend.app.engine.search_engine import ASOSSearchEngine
from backend.app.models.search import (
    SearchRequest, SearchResponse, EvaluateRequest,
)
from backend.app.models.product import SimilarResponse
from backend.app.services import search_service

logger = logging.getLogger("asos_search")

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def text_search(
    request: SearchRequest,
    engine: ASOSSearchEngine = Depends(get_engine),
) -> SearchResponse:
    """Text search with optional base64 image for multimodal queries."""
    return search_service.search(engine, request)


@router.post("/image", response_model=SearchResponse)
async def image_search(
    file: UploadFile = File(...),
    top_n: int = Query(20, ge=1, le=100),
    engine: ASOSSearchEngine = Depends(get_engine),
) -> SearchResponse:
    """Image-only search via file upload."""
    image_bytes = await file.read()
    image = search_service.decode_image(image_bytes=image_bytes)
    return search_service.search_by_image(engine, image, top_n=top_n)


@router.get("/similar/{sku}", response_model=SimilarResponse)
def similar_search(
    sku: str,
    top_n: int = Query(10, ge=1, le=100),
    engine: ASOSSearchEngine = Depends(get_engine),
) -> SimilarResponse:
    """Find visually similar products to a given SKU."""
    return search_service.get_similar(engine, sku, top_n=top_n)


@router.post("/evaluate")
def evaluate(
    request: EvaluateRequest,
    engine: ASOSSearchEngine = Depends(get_engine),
) -> dict:
    """Run evaluation suite against the engine."""
    from backend.app.engine.evaluator import SearchEvaluator
    evaluator = SearchEvaluator(engine)
    return evaluator.evaluate(request.test_queries, k_values=request.k_values)
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/routers/search.py
git commit -m "feat: add search, image search, similar, and evaluate endpoints"
```

### Task 15: routers/products.py

**Files:**
- Create: `backend/app/routers/products.py`

- [ ] **Step 1: Create products.py**

```python
from fastapi import APIRouter, Depends, Query

from backend.app.dependencies import get_engine
from backend.app.engine.search_engine import ASOSSearchEngine
from backend.app.models.product import ProductDetail, OutfitResponse
from backend.app.services import search_service

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/{sku}", response_model=ProductDetail)
def product_detail(
    sku: str,
    engine: ASOSSearchEngine = Depends(get_engine),
) -> ProductDetail:
    """Get full product details for a single SKU."""
    return search_service.get_product_detail(engine, sku)


@router.get("/{sku}/outfit", response_model=OutfitResponse)
def complete_the_look(
    sku: str,
    n_per_category: int = Query(3, ge=1, le=10),
    engine: ASOSSearchEngine = Depends(get_engine),
) -> OutfitResponse:
    """Get outfit recommendations for a product."""
    return search_service.get_outfit(engine, sku, n_per_category=n_per_category)
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/routers/products.py
git commit -m "feat: add product detail and outfit recommendation endpoints"
```

### Task 16: main.py — FastAPI app

**Files:**
- Create: `backend/app/main.py`

- [ ] **Step 1: Create main.py**

```python
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import Settings, SearchConfig
from backend.app.exceptions import EngineNotReadyError, SKUNotFoundError, InvalidQueryError
from backend.app.engine.search_engine import ASOSSearchEngine
from backend.app.routers import health, search, products

settings = Settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("asos_search")

for _noisy in ("urllib3", "urllib3.connectionpool", "requests", "PIL",
               "transformers", "transformers.modeling_utils"):
    logging.getLogger(_noisy).setLevel(logging.ERROR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load engine at startup, clean up on shutdown."""
    logger.info("Starting ASOS Search Engine...")
    config = SearchConfig.from_settings(settings)
    engine = ASOSSearchEngine(config)
    engine.load_data()
    engine.build_index()
    app.state.engine = engine
    logger.info(f"Engine ready with {len(engine.metadata):,} products")
    yield
    logger.info("Shutting down ASOS Search Engine.")


app = FastAPI(
    title="ASOS Fashion Search API",
    description="Multimodal, intent-driven semantic search engine for fashion products",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")


# Exception handlers
@app.exception_handler(EngineNotReadyError)
async def engine_not_ready_handler(request: Request, exc: EngineNotReadyError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(SKUNotFoundError)
async def sku_not_found_handler(request: Request, exc: SKUNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(InvalidQueryError)
async def invalid_query_handler(request: Request, exc: InvalidQueryError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: FastAPI app with lifespan, CORS, routers, and exception handlers"
```

---

## Phase 4: Tests

### Task 17: conftest.py + test_query_parser.py

**Files:**
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_query_parser.py`

- [ ] **Step 1: Create conftest.py**

```python
import pytest


@pytest.fixture
def query_parser():
    from backend.app.engine.query_parser import QueryParser
    return QueryParser()
```

- [ ] **Step 2: Create test_query_parser.py**

```python
import pytest
from backend.app.engine.query_parser import QueryParser, ParsedQuery


@pytest.fixture
def parser():
    return QueryParser()


class TestCategoryParsing:
    def test_dress(self, parser):
        result = parser.parse("black midi dress")
        assert result.category_filter == "Dresses"

    def test_jacket(self, parser):
        result = parser.parse("leather jacket")
        assert result.category_filter == "Coats & Jackets"

    def test_jeans(self, parser):
        result = parser.parse("blue jeans")
        assert result.category_filter == "Jeans"

    def test_hoodie(self, parser):
        result = parser.parse("oversized hoodie")
        assert result.category_filter == "Hoodies & Sweatshirts"

    def test_no_category(self, parser):
        result = parser.parse("something nice")
        assert result.category_filter is None


class TestColorParsing:
    def test_basic_color(self, parser):
        result = parser.parse("black dress")
        assert result.color_filter == "black"

    def test_synonym_color(self, parser):
        result = parser.parse("scarlet top")
        assert result.color_filter == "red"

    def test_navy(self, parser):
        result = parser.parse("navy blazer")
        assert result.color_filter == "navy"

    def test_no_color(self, parser):
        result = parser.parse("casual hoodie")
        assert result.color_filter is None


class TestPriceParsing:
    def test_under(self, parser):
        result = parser.parse("dress under £40")
        assert result.price_max == 40.0
        assert result.price_min is None

    def test_over(self, parser):
        result = parser.parse("jacket over £100")
        assert result.price_min == 100.0

    def test_range(self, parser):
        result = parser.parse("shoes £20-£50")
        assert result.price_min == 20.0
        assert result.price_max == 50.0

    def test_budget(self, parser):
        result = parser.parse("budget dress")
        assert result.price_max == 30.0

    def test_luxury(self, parser):
        result = parser.parse("luxury jacket")
        assert result.price_min == 100.0


class TestGenderParsing:
    def test_mens(self, parser):
        result = parser.parse("mens hoodie")
        assert result.gender_filter == "Men"

    def test_womens(self, parser):
        result = parser.parse("women's dress")
        assert result.gender_filter == "Women"


class TestMaterialParsing:
    def test_silk(self, parser):
        result = parser.parse("silk midi dress")
        assert result.material_filter == "silk"

    def test_leather(self, parser):
        result = parser.parse("leather jacket")
        assert result.material_filter == "leather"

    def test_no_material(self, parser):
        result = parser.parse("black dress")
        assert result.material_filter is None


class TestSizeParsing:
    def test_named_size(self, parser):
        result = parser.parse("size small hoodie")
        assert result.size_filter == "S"

    def test_numeric_size(self, parser):
        result = parser.parse("size 10 dress")
        assert result.size_filter == "10"

    def test_xl(self, parser):
        result = parser.parse("XL casual shirt")
        assert result.size_filter == "XL"


class TestExclusions:
    def test_not(self, parser):
        result = parser.parse("black dress not floral")
        assert "floral" in result.exclusions

    def test_without(self, parser):
        result = parser.parse("jacket without leather")
        assert "leather" in result.exclusions

    def test_material_exclusion_conflict(self, parser):
        result = parser.parse("jacket not cotton")
        assert result.material_filter is None
        assert "cotton" in result.exclusions


class TestStyleTags:
    def test_single_tag(self, parser):
        result = parser.parse("casual hoodie")
        assert "casual" in result.style_tags

    def test_multiple_tags(self, parser):
        result = parser.parse("vintage boho dress")
        assert "vintage" in result.style_tags
        assert "boho" in result.style_tags


class TestVibeText:
    def test_preserves_query(self, parser):
        result = parser.parse("black dress")
        assert result.raw_query == "black dress"
        assert len(result.vibe_text) > 0
```

- [ ] **Step 3: Run tests**

```bash
cd backend && python -m pytest tests/test_query_parser.py -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/tests/
git commit -m "test: add comprehensive query parser tests"
```

### Task 18: test_nlp.py

**Files:**
- Create: `backend/tests/test_nlp.py`

- [ ] **Step 1: Create test_nlp.py**

```python
from backend.app.engine.nlp import MultilingualHandler, SpellCorrector


class TestMultilingualHandler:
    def test_english_detected(self):
        lang = MultilingualHandler.detect_language("black leather jacket")
        assert lang == "en"

    def test_french_detected(self):
        lang = MultilingualHandler.detect_language("robe noir pour la femme")
        assert lang == "fr"

    def test_german_detected(self):
        lang = MultilingualHandler.detect_language("das kleid ist für die frau")
        assert lang == "de"

    def test_translate_french(self):
        translated, lang, was_translated = MultilingualHandler.translate_query("robe noir")
        assert "dress" in translated
        assert "black" in translated
        assert was_translated is True

    def test_english_passthrough(self):
        translated, lang, was_translated = MultilingualHandler.translate_query("black dress")
        assert translated == "black dress"
        assert was_translated is False

    def test_spanish_translate(self):
        translated, lang, was_translated = MultilingualHandler.translate_query("vestido rojo")
        assert "dress" in translated
        assert "red" in translated


class TestSpellCorrector:
    def test_correct_known_word(self):
        sc = SpellCorrector()
        sc.fit(["black leather jacket dress shoes boots"])
        corrected = sc.correct_word("blak")
        assert corrected == "black"

    def test_no_correction_needed(self):
        sc = SpellCorrector()
        sc.fit(["black leather jacket"])
        corrected = sc.correct_word("black")
        assert corrected == "black"

    def test_query_correction(self):
        sc = SpellCorrector()
        sc.fit(["black leather jacket dress shoes boots trainers hoodie"])
        result, was_corrected = sc.correct_query("blak lether jaket")
        assert was_corrected is True
        assert "black" in result

    def test_short_words_skipped(self):
        sc = SpellCorrector()
        sc.fit(["black leather jacket"])
        corrected = sc.correct_word("an")
        assert corrected == "an"

    def test_price_tokens_skipped(self):
        sc = SpellCorrector()
        sc.fit(["black dress"])
        result, _ = sc.correct_query("dress £40")
        assert "£40" in result
```

- [ ] **Step 2: Run tests**

```bash
cd backend && python -m pytest tests/test_nlp.py -v
```

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_nlp.py
git commit -m "test: add multilingual handler and spell corrector tests"
```

### Task 19: test_bm25.py

**Files:**
- Create: `backend/tests/test_bm25.py`

- [ ] **Step 1: Create test_bm25.py**

```python
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
```

- [ ] **Step 2: Run tests**

```bash
cd backend && python -m pytest tests/test_bm25.py -v
```

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_bm25.py
git commit -m "test: add BM25 scorer tests"
```

### Task 20: API tests

**Files:**
- Create: `backend/tests/test_api_health.py`
- Create: `backend/tests/test_api_search.py`
- Create: `backend/tests/test_api_products.py`

- [ ] **Step 1: Create test_api_health.py**

```python
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from backend.app.main import app


def _make_mock_engine(ready=True, n_products=100):
    engine = MagicMock()
    engine._is_ready = ready
    engine.metadata = MagicMock()
    engine.metadata.__len__ = MagicMock(return_value=n_products)
    engine.audit.return_value = {"status": "ready", "products": n_products}
    return engine


class TestHealthEndpoints:
    def test_health_ok(self):
        client = TestClient(app, raise_server_exceptions=False)
        app.state.engine = _make_mock_engine()
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["engine_ready"] is True

    def test_health_not_ready(self):
        client = TestClient(app, raise_server_exceptions=False)
        app.state.engine = _make_mock_engine(ready=False)
        response = client.get("/api/v1/health")
        data = response.json()
        assert data["engine_ready"] is False

    def test_audit(self):
        client = TestClient(app, raise_server_exceptions=False)
        app.state.engine = _make_mock_engine()
        response = client.get("/api/v1/audit")
        assert response.status_code == 200
```

- [ ] **Step 2: Create test_api_search.py**

```python
from unittest.mock import MagicMock, patch
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


class TestSearchEndpoints:
    def test_text_search(self):
        engine = MagicMock()
        engine._is_ready = True
        engine.search.return_value = _make_search_results()
        app.state.engine = engine

        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/api/v1/search", json={"query": "black dress"})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["results"][0]["sku"] == "12345"
        assert data["query_info"]["parsed_category"] == "Dresses"

    def test_empty_query_rejected(self):
        engine = MagicMock()
        engine._is_ready = True
        app.state.engine = engine

        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/api/v1/search", json={"query": ""})
        assert response.status_code == 422

    def test_engine_not_ready(self):
        app.state.engine = None
        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/api/v1/search", json={"query": "dress"})
        assert response.status_code == 503
```

- [ ] **Step 3: Create test_api_products.py**

```python
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from backend.app.main import app


class TestProductEndpoints:
    def test_product_detail(self):
        engine = MagicMock()
        engine._is_ready = True
        engine.get_product_detail.return_value = {
            "sku": "12345", "name": "Test Dress", "brand": "ASOS",
            "price": 29.99, "color_clean": "black", "color_family": "black",
            "category": "Dresses", "gender": "Women",
            "primary_image_url": "https://example.com/img.jpg",
            "image_urls": ["https://example.com/img.jpg"],
            "style_tags": [], "materials": [], "sizes_available": [],
            "product_details": "A nice dress", "any_in_stock": True,
        }
        app.state.engine = engine

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/products/12345")
        assert response.status_code == 200
        assert response.json()["sku"] == "12345"

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
        engine.get_product_detail.return_value = {
            "sku": "12345", "name": "Test Dress", "brand": "ASOS",
            "price": 29.99, "color_clean": "black", "color_family": "black",
            "category": "Dresses", "gender": "Women",
            "primary_image_url": "https://example.com/img.jpg",
            "image_urls": [], "style_tags": [], "materials": [],
            "sizes_available": [], "product_details": "", "any_in_stock": True,
        }
        engine.complete_the_look.return_value = {}
        app.state.engine = engine

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/products/12345/outfit")
        assert response.status_code == 200
        assert "outfit" in response.json()
```

- [ ] **Step 4: Run all tests**

```bash
cd backend && python -m pytest tests/ -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/tests/
git commit -m "test: add API endpoint tests for health, search, and products"
```

---

## Phase 5: Documentation

### Task 21: Create all documentation files

**Files:**
- Create: `documentation/CLAUDE.md`
- Create: `documentation/techstack.md`
- Create: `documentation/prd.md`
- Create: `documentation/progress.md`
- Create: `documentation/plan.md`
- Create: `documentation/architecture.md`
- Create: `documentation/flow.md`
- Create: `README.md`

- [ ] **Step 1: Create all 8 documentation files**

Each file must be concise (<170 words) and provide enough context for a coding agent. Content specified during implementation based on the final codebase state.

- [ ] **Step 2: Commit**

```bash
git add documentation/ README.md
git commit -m "docs: add project documentation suite"
```
