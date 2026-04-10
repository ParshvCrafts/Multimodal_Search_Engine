import logging
from collections import Counter
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from backend.app.config import SearchConfig
from backend.app.engine.query_parser import ParsedQuery
from backend.app.engine.bm25 import SimpleBM25

logger = logging.getLogger("asos_search")

__all__ = [
    "apply_filters",
    "relax_and_retry",
    "hybrid_rerank",
    "generate_suggestions",
]


def apply_filters(candidates: pd.DataFrame, parsed: ParsedQuery) -> pd.DataFrame:
    df = candidates
    if parsed.category_filter and 'category' in df.columns:
        df = df[df['category'] == parsed.category_filter]
    if parsed.color_filter and 'color_family' in df.columns:
        df = df[df['color_family'].str.lower() == parsed.color_filter.lower()]
    if parsed.gender_filter and 'gender' in df.columns:
        df = df[(df['gender'] == parsed.gender_filter) | (df['gender'] == 'Unisex')]
    if parsed.price_min is not None and 'price' in df.columns:
        df = df[df['price'] >= parsed.price_min]
    if parsed.price_max is not None and 'price' in df.columns:
        df = df[df['price'] <= parsed.price_max]
    if parsed.brand_filter and 'brand' in df.columns:
        df = df[df['brand'].str.lower() == parsed.brand_filter.lower()]

    # ── Size filtering (v3.3) ──
    if parsed.size_filter and 'sizes_available' in df.columns:
        size_val = parsed.size_filter.lower().strip()
        df = df[df['sizes_available'].apply(
            lambda sizes: any(
                size_val == str(s).lower().strip()
                for s in (sizes if isinstance(sizes, list) else [])
            ) if isinstance(sizes, list) else False
        )]

    # ── Material filtering (v3.3) ──
    if parsed.material_filter and 'materials' in df.columns:
        mat = parsed.material_filter.lower()
        df = df[df['materials'].apply(
            lambda mats: (
                any(mat in str(m).lower() for m in mats)
                if isinstance(mats, list) and len(mats) > 0
                else mat in str(mats).lower() if mats else False
            )
        )]

    # ── Exclusion filtering (v3.3) ──
    if parsed.exclusions:
        for excl in parsed.exclusions:
            excl_lower = excl.lower()
            # Check against name, color, category, style_tags, materials
            mask = pd.Series(True, index=df.index)
            if 'name' in df.columns:
                mask &= ~df['name'].str.lower().str.contains(excl_lower, na=False)
            if 'color_clean' in df.columns:
                mask &= ~df['color_clean'].str.lower().str.contains(excl_lower, na=False)
            if 'color_family' in df.columns:
                mask &= ~(df['color_family'].str.lower() == excl_lower)
            if 'style_tags' in df.columns:
                mask &= ~df['style_tags'].apply(
                    lambda tags: any(excl_lower in str(t).lower() for t in tags)
                    if isinstance(tags, list) else False
                )
            if 'materials' in df.columns:
                mask &= ~df['materials'].apply(
                    lambda mats: any(excl_lower in str(m).lower()
                                     for m in (mats if isinstance(mats, list) else []))
                )
            df = df[mask]

    if parsed.in_stock_only and 'any_in_stock' in df.columns:
        df = df[df['any_in_stock'] == True]
    return df


def relax_and_retry(candidates: pd.DataFrame, parsed: ParsedQuery,
                    min_results: int = 10) -> pd.DataFrame:
    """
    Smart progressive filter relaxation.

    Key improvement: instead of dropping price_max entirely (which shows
    £200 items for "under £10"), we progressively expand the budget in
    steps (×1.5, ×2, ×3, ×5) so the user sees the cheapest viable options.
    """
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

    # Phase 0: Try relaxing size and material first (least important constraints)
    # Try each independently before committing
    for attr in ('size_filter', 'material_filter'):
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
                setattr(relaxed, attr, saved)  # restore if it didn't help

    # Phase 0b: Relax exclusions if they're too restrictive
    if relaxed.exclusions:
        relaxed.exclusions = []
        result = apply_filters(candidates, relaxed)
        if len(result) > len(best_so_far):
            best_so_far = result
        if len(result) >= min_results:
            logger.info(f"Relaxed exclusions -> {len(result)} results")
            return result

    # Phase 1: Try relaxing non-price filters one by one
    non_price_relaxations = [
        ('color_filter', None), ('gender_filter', None), ('in_stock_only', False),
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

    # Phase 2: Progressive price expansion (keep category if possible)
    if parsed.price_max is not None:
        original_max = parsed.price_max
        expansion_factors = [1.5, 2.0, 3.0, 5.0, 10.0]
        for factor in expansion_factors:
            relaxed.price_max = original_max * factor
            result = apply_filters(candidates, relaxed)
            if len(result) > len(best_so_far):
                best_so_far = result
            if len(result) >= min_results:
                logger.info(
                    f"Expanded price_max: £{original_max:.0f} -> "
                    f"£{relaxed.price_max:.0f} ({factor}×) -> {len(result)} results"
                )
                return result

        # If even 10× doesn't work, drop the price filter
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

    # Phase 3: Drop category as last resort
    if relaxed.category_filter is not None:
        relaxed.category_filter = None
        result = apply_filters(candidates, relaxed)
        if len(result) > len(best_so_far):
            best_so_far = result
        if len(result) >= min_results:
            logger.info(f"Relaxed category_filter -> {len(result)} results")
            return result

    # Return best partial result even if < min_results
    if len(best_so_far) > 0:
        logger.info(f"Returning best available: {len(best_so_far)} results (wanted {min_results})")
        return best_so_far

    logger.warning("All filters relaxed. Returning unfiltered results.")
    return candidates


def hybrid_rerank(candidates: pd.DataFrame, parsed: ParsedQuery,
                  config: SearchConfig, bm25: Optional[SimpleBM25] = None) -> pd.DataFrame:
    scored = candidates.copy()
    if len(scored) == 0:
        return scored

    # Normalize RRF
    rrf_vals = scored['rrf_score'].values
    rrf_min, rrf_max = rrf_vals.min(), rrf_vals.max()
    scored['rrf_norm'] = (
        (rrf_vals - rrf_min) / (rrf_max - rrf_min) if rrf_max > rrf_min else 1.0
    )

    # Tag overlap
    query_tags = set(parsed.style_tags)
    if query_tags and 'style_tags' in scored.columns:
        scored['tag_score'] = scored['style_tags'].apply(
            lambda tags: (
                len(set(tags) & query_tags) / len(query_tags)
                if isinstance(tags, list) and query_tags else 0.0
            )
        )
    else:
        scored['tag_score'] = 0.0

    # BM25
    if bm25 is not None and '_orig_idx' in scored.columns:
        bm25_raw = bm25.score_candidates(parsed.raw_query, scored['_orig_idx'].tolist())
        bm25_max = bm25_raw.max()
        scored['bm25_norm'] = bm25_raw / bm25_max if bm25_max > 0 else 0.0
    else:
        scored['bm25_norm'] = 0.0

    # Stock bonus
    if 'any_in_stock' in scored.columns:
        scored['stock_bonus'] = scored['any_in_stock'].astype(float)
    else:
        scored['stock_bonus'] = 0.5

    # ── Material match bonus (v3.3) ──
    mat_bonus = np.zeros(len(scored), dtype=np.float32)
    if parsed.material_filter and 'materials' in scored.columns:
        mat_q = parsed.material_filter.lower()
        mat_bonus = scored['materials'].apply(
            lambda mats: 1.0 if isinstance(mats, list) and any(
                mat_q in str(m).lower() for m in mats
            ) else 0.0
        ).values.astype(np.float32)
    scored['material_bonus'] = mat_bonus

    # ── Price proximity bonus ──
    # When user specifies a budget, items closer to that price rank higher.
    # This prevents £200 items outranking £20 items when user said "under £10".
    price_proximity = np.zeros(len(scored), dtype=np.float32)
    target_price = parsed.price_max or parsed.price_min
    if target_price is not None and 'price' in scored.columns:
        prices = scored['price'].values.astype(np.float32)
        # Exponential decay: items at target_price get 1.0, items far away get ~0
        # sigma controls how fast the penalty drops off
        sigma = max(target_price * 0.5, 10.0)  # half the budget or £10 minimum
        price_proximity = np.exp(-((prices - target_price) ** 2) / (2 * sigma ** 2))

    scored['price_proximity'] = price_proximity

    # Weighted combination — price proximity gets 0.10 weight when active
    has_price_intent = target_price is not None
    has_material_intent = parsed.material_filter is not None

    if has_price_intent:
        scored['hybrid_score'] = (
            0.40 * scored['rrf_norm'] +
            0.18 * scored['tag_score'] +
            0.10 * scored['bm25_norm'] +
            0.05 * scored['stock_bonus'] +
            0.20 * scored['price_proximity'] +
            0.07 * scored['material_bonus']
        )
    elif has_material_intent:
        scored['hybrid_score'] = (
            0.45 * scored['rrf_norm'] +
            0.20 * scored['tag_score'] +
            0.12 * scored['bm25_norm'] +
            0.05 * scored['stock_bonus'] +
            0.18 * scored['material_bonus']
        )
    else:
        scored['hybrid_score'] = (
            config.alpha_clip * scored['rrf_norm'] +
            config.beta_tags * scored['tag_score'] +
            config.gamma_text * scored['bm25_norm'] +
            config.delta_freshness * scored['stock_bonus']
        )
    return scored.sort_values('hybrid_score', ascending=False)


def generate_suggestions(results: pd.DataFrame, parsed: ParsedQuery,
                         max_suggestions: int = 5) -> List[str]:
    """
    Generate natural, diverse related search suggestions.

    v3.3: produces clean, human-readable queries instead of awkward
    concatenations. Covers color refinement, price ranges, category
    alternatives, style variations, and brand-specific searches.
    """
    if len(results) == 0:
        return []

    suggestions = []

    # Extract core item type from the query for clean suggestion construction
    cat = parsed.category_filter
    cat_names = {
        'Dresses': 'dresses', 'Tops': 'tops', 'Coats & Jackets': 'jackets',
        'Knitwear': 'knitwear', 'Jeans': 'jeans', 'Trousers': 'trousers',
        'Shoes': 'shoes', 'Bags': 'bags', 'Accessories': 'accessories',
        'Skirts': 'skirts', 'Shorts': 'shorts', 'Swimwear': 'swimwear',
        'Hoodies & Sweatshirts': 'hoodies', 'Suits & Tailoring': 'suits',
        'Jumpsuits & Playsuits': 'jumpsuits',
    }
    base_term = cat_names.get(cat, parsed.vibe_text.strip()[:30])

    # 1. Color refinements — suggest specific colors the user hasn't tried
    if 'color_family' in results.columns and not parsed.color_filter:
        top_colors = (results['color_family']
                     .value_counts()
                     .head(4).index.tolist())
        for color in top_colors[:2]:
            if color and color not in ('other', 'multi'):
                suggestions.append(f"{color} {base_term}")

    # 2. Alternate color if user specified one
    if parsed.color_filter and 'color_family' in results.columns:
        alt_colors = ['black', 'white', 'navy', 'beige']
        for ac in alt_colors:
            if ac != parsed.color_filter:
                suggestions.append(f"{ac} {base_term}")
                break

    # 3. Price-constrained suggestion
    if parsed.price_max is None and parsed.price_min is None and 'price' in results.columns:
        p25 = results['price'].quantile(0.25)
        if p25 > 5:
            suggestions.append(f"{base_term} under \u00a3{int(p25)}")

    # 4. Style variation — suggest a popular style tag from results
    if 'style_tags' in results.columns:
        tag_counts = Counter()
        for tags in results['style_tags']:
            if isinstance(tags, list):
                for t in tags:
                    if t not in parsed.style_tags and t not in parsed.vibe_text:
                        tag_counts[t] += 1
        if tag_counts:
            best_tag = tag_counts.most_common(1)[0][0]
            suggestions.append(f"{best_tag} {base_term}")

    # 5. Brand-specific suggestion (clean format)
    if 'brand' in results.columns:
        top_brand = (results['brand']
                    .value_counts()
                    .head(1).index.tolist())
        if top_brand and top_brand[0] and top_brand[0] != 'Unknown':
            brand = top_brand[0]
            if brand.lower() not in parsed.vibe_text.lower():
                suggestions.append(f"{brand} {base_term}")

    # 6. Category alternatives — suggest related categories
    if cat:
        related = {
            'Dresses': 'jumpsuits', 'Tops': 'blouses',
            'Jeans': 'trousers', 'Trousers': 'jeans',
            'Coats & Jackets': 'blazers', 'Knitwear': 'cardigans',
            'Skirts': 'dresses', 'Shorts': 'skirts',
        }
        alt = related.get(cat)
        if alt:
            prefix = f"{parsed.color_filter} " if parsed.color_filter else ""
            suggestions.append(f"{prefix}{alt}".strip())

    # Deduplicate and limit
    seen = set()
    unique = []
    for s in suggestions:
        s_clean = s.strip().lower()
        if s_clean not in seen and s_clean != parsed.raw_query.lower():
            seen.add(s_clean)
            unique.append(s.strip())
    return unique[:max_suggestions]
