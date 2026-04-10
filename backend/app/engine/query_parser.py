"""
engine/query_parser.py

Extracted from finalized_search_engine_full_script.py (lines 776-1056).
Contains the ParsedQuery dataclass and QueryParser class responsible for
converting natural-language fashion queries into structured filter intents.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)

__all__ = ["ParsedQuery", "QueryParser"]


@dataclass
class ParsedQuery:
    raw_query: str
    vibe_text: str

    category_filter: Optional[str] = None
    color_filter: Optional[str] = None
    gender_filter: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    brand_filter: Optional[str] = None
    size_filter: Optional[str] = None
    material_filter: Optional[str] = None
    exclusions: List[str] = field(default_factory=list)
    in_stock_only: bool = True

    style_tags: List[str] = field(default_factory=list)

    has_image: bool = False
    text_weight: float = 0.5

    # Multilingual / correction metadata
    original_query: Optional[str] = None
    detected_language: str = "en"
    was_translated: bool = False
    was_spell_corrected: bool = False
    spell_correction_suggestion: Optional[str] = None


class QueryParser:
    """Parses natural language fashion queries into structured intents."""

    PRICE_PATTERNS = [
        (r'[£$€]?\s*(\d+(?:\.\d+)?)\s*[-–to]+\s*[£$€]?\s*(\d+(?:\.\d+)?)', 'range'),
        (r'(?:under|below|less\s+than|max|up\s+to|cheaper\s+than)\s*[£$€]?\s*(\d+(?:\.\d+)?)', 'max'),
        (r'(?:over|above|more\s+than|min|at\s+least|from)\s*[£$€]?\s*(\d+(?:\.\d+)?)', 'min'),
        (r'\b(?:budget|cheap|affordable|bargain|inexpensive|value)\b', 'budget'),
        (r'\b(?:luxury|premium|high[\s-]?end|designer|expensive|splurge)\b', 'luxury'),
    ]

    CATEGORY_TRIGGERS = {
        'midi dress': 'Dresses', 'maxi dress': 'Dresses',
        'mini dress': 'Dresses', 'slip dress': 'Dresses',
        'bodycon': 'Dresses', 'dress': 'Dresses',
        'dresses': 'Dresses', 'gown': 'Dresses',

        'trench coat': 'Coats & Jackets', 'puffer jacket': 'Coats & Jackets',
        'leather jacket': 'Coats & Jackets', 'denim jacket': 'Coats & Jackets',
        'bomber jacket': 'Coats & Jackets',
        'jacket': 'Coats & Jackets', 'coat': 'Coats & Jackets',
        'blazer': 'Coats & Jackets', 'parka': 'Coats & Jackets',

        't-shirt': 'Tops', 'tee': 'Tops',
        'blouse': 'Tops', 'shirt': 'Tops',
        'crop top': 'Tops', 'cami': 'Tops',
        'bodysuit': 'Tops', 'top': 'Tops', 'tops': 'Tops',

        'cardigan': 'Knitwear', 'jumper': 'Knitwear',
        'sweater': 'Knitwear', 'pullover': 'Knitwear', 'knitwear': 'Knitwear',

        'hoodie': 'Hoodies & Sweatshirts', 'sweatshirt': 'Hoodies & Sweatshirts',

        'jeans': 'Jeans',
        'trousers': 'Trousers', 'pants': 'Trousers',
        'joggers': 'Trousers', 'leggings': 'Trousers', 'cargo': 'Trousers',

        'shorts': 'Shorts',

        'skirt': 'Skirts', 'midi skirt': 'Skirts', 'mini skirt': 'Skirts',

        'trainers': 'Shoes', 'sneakers': 'Shoes',
        'boots': 'Shoes', 'heels': 'Shoes',
        'sandals': 'Shoes', 'loafers': 'Shoes',
        'shoes': 'Shoes', 'mules': 'Shoes',
        'platforms': 'Shoes', 'flats': 'Shoes',

        'bag': 'Bags', 'handbag': 'Bags',
        'tote': 'Bags', 'backpack': 'Bags',
        'clutch': 'Bags', 'crossbody': 'Bags',

        'watch': 'Accessories', 'sunglasses': 'Accessories',
        'hat': 'Accessories', 'cap': 'Accessories',
        'scarf': 'Accessories', 'belt': 'Accessories',
        'jewellery': 'Accessories', 'jewelry': 'Accessories',
        'necklace': 'Accessories', 'bracelet': 'Accessories',
        'earrings': 'Accessories', 'ring': 'Accessories',

        'swimsuit': 'Swimwear', 'bikini': 'Swimwear', 'swim': 'Swimwear',
        'suit': 'Suits & Tailoring', 'waistcoat': 'Suits & Tailoring',
        'jumpsuit': 'Jumpsuits & Playsuits', 'playsuit': 'Jumpsuits & Playsuits',
        'romper': 'Jumpsuits & Playsuits',
        'lingerie': 'Underwear & Socks', 'bra': 'Underwear & Socks',
        'briefs': 'Underwear & Socks', 'boxers': 'Underwear & Socks',
        'socks': 'Underwear & Socks',
    }

    # ── FIX: COLOR_MAP now outputs LOWERCASE to match actual data values ──
    COLOR_MAP = {
        'red': 'red', 'scarlet': 'red', 'crimson': 'red',
        'blue': 'blue', 'cobalt': 'blue',
        'sky blue': 'blue', 'teal': 'blue', 'aqua': 'blue',
        'navy': 'navy',  # data has 'navy' as its own family
        'green': 'green', 'olive': 'green', 'emerald': 'green',
        'sage': 'green', 'mint': 'green',
        'khaki': 'khaki',  # data has 'khaki' as its own family
        'black': 'black', 'charcoal': 'black',
        'white': 'white', 'cream': 'white', 'ivory': 'white',
        'pink': 'pink', 'blush': 'pink', 'rose': 'pink',
        'fuchsia': 'pink', 'magenta': 'pink', 'coral': 'pink',
        'yellow': 'yellow', 'gold': 'yellow', 'mustard': 'yellow',
        'orange': 'orange', 'rust': 'orange', 'terracotta': 'orange',
        'brown': 'brown', 'tan': 'brown', 'camel': 'brown',
        'beige': 'beige', 'taupe': 'beige',  # data has 'beige' as its own family
        'chocolate': 'brown',
        'purple': 'purple', 'lilac': 'purple', 'plum': 'purple',
        'lavender': 'purple', 'violet': 'purple', 'mauve': 'purple',
        'burgundy': 'burgundy',  # data has 'burgundy' as its own family
        'grey': 'grey', 'gray': 'grey', 'silver': 'grey',
        'multi': 'multi', 'rainbow': 'multi', 'multicolour': 'multi',
        'multicolor': 'multi',
    }

    GENDER_TRIGGERS = {
        "men's": "Men", "mens": "Men", "male": "Men", "for men": "Men",
        "for him": "Men", "boys": "Men", "masculine": "Men",
        "women's": "Women", "womens": "Women", "female": "Women",
        "for women": "Women", "for her": "Women", "girls": "Women",
        "ladies": "Women", "feminine": "Women",
        "unisex": "Unisex",
    }

    STYLE_TAGS = [
        'casual', 'formal', 'streetwear', 'boho', 'bohemian', 'minimalist',
        'vintage', 'retro', 'y2k', 'goth', 'gothic', 'punk', 'preppy',
        'athleisure', 'sporty', 'elegant', 'chic', 'edgy', 'romantic',
        'classic', 'modern', 'oversized', 'cropped', 'fitted', 'relaxed',
        'floral', 'striped', 'plaid', 'animal print', 'leopard', 'sequin',
        'lace', 'denim', 'leather', 'satin', 'silk', 'velvet', 'knit',
        'sustainable', 'eco', 'organic', 'recycled',
        'festival', 'party', 'office', 'workwear', 'loungewear', 'sleepwear',
        'coastal', 'cottagecore', 'grunge', 'cyber', 'futuristic',
        'western', 'nautical', 'tropical', 'safari',
    ]

    MATERIAL_KEYWORDS = {
        'silk': 'silk', 'satin': 'satin', 'velvet': 'velvet',
        'leather': 'leather', 'faux leather': 'faux leather',
        'denim': 'denim', 'cotton': 'cotton', 'linen': 'linen',
        'wool': 'wool', 'cashmere': 'cashmere', 'polyester': 'polyester',
        'nylon': 'nylon', 'suede': 'suede', 'chiffon': 'chiffon',
        'mesh': 'mesh', 'jersey': 'jersey',
        'tweed': 'tweed', 'corduroy': 'corduroy', 'fleece': 'fleece',
        'crochet': 'crochet', 'organza': 'organza', 'tulle': 'tulle',
    }

    SIZE_PATTERNS = [
        (r'\bsize\s+(xx?s|xx?l|small|medium|large)\b', 'named'),
        (r'\b(xx?s|xx?l)\b', 'named_bare'),
        (r'\bsize\s+(\d{1,2})\b', 'numeric'),
        (r'\buk\s+(\d{1,2})\b', 'numeric'),
        (r'\beu\s+(\d{2})\b', 'eu'),
    ]

    _SIZE_NORMALIZE = {
        'xxs': 'XXS', 'xs': 'XS', 'x-small': 'XS', 'xsmall': 'XS',
        's': 'S', 'small': 'S',
        'm': 'M', 'medium': 'M',
        'l': 'L', 'large': 'L',
        'xl': 'XL', 'x-large': 'XL', 'xlarge': 'XL',
        'xxl': 'XXL',
    }

    EXCLUSION_PATTERNS = [
        r'\bnot\s+(\w+(?:\s+\w+)?)',
        r'\bwithout\s+(\w+(?:\s+\w+)?)',
        r'\bno\s+(\w+)',
        r'\bexcluding\s+(\w+(?:\s+\w+)?)',
    ]

    def parse(self, query: str) -> ParsedQuery:
        raw = query.strip()
        q = raw.lower()
        vibe = q

        # Price
        price_min, price_max = None, None
        for pattern, ptype in self.PRICE_PATTERNS:
            m = re.search(pattern, q)
            if m:
                if ptype == 'range':
                    price_min, price_max = float(m.group(1)), float(m.group(2))
                elif ptype == 'max':
                    price_max = float(m.group(1))
                elif ptype == 'min':
                    price_min = float(m.group(1))
                elif ptype == 'budget':
                    price_max = 30.0
                elif ptype == 'luxury':
                    price_min = 100.0
                vibe = vibe[:m.start()] + vibe[m.end():]
                break

        # Category
        category = None
        for trigger, cat in sorted(self.CATEGORY_TRIGGERS.items(), key=lambda x: -len(x[0])):
            if re.search(r'\b' + re.escape(trigger) + r'\b', q):
                category = cat
                break

        # Color
        color = None
        for color_term, family in sorted(self.COLOR_MAP.items(), key=lambda x: -len(x[0])):
            if re.search(r'\b' + re.escape(color_term) + r'\b', q):
                color = family
                break

        # Gender
        gender = None
        for trigger, gen in self.GENDER_TRIGGERS.items():
            if trigger in q:
                gender = gen
                vibe = vibe.replace(trigger, '')
                break

        # Style tags
        tags = [t for t in self.STYLE_TAGS if re.search(r'\b' + re.escape(t) + r'\b', q)]

        # Material
        material = None
        for mat_term, mat_val in sorted(self.MATERIAL_KEYWORDS.items(), key=lambda x: -len(x[0])):
            if re.search(r'\b' + re.escape(mat_term) + r'\b', q):
                material = mat_val
                break

        # Size
        size = None
        for pattern, stype in self.SIZE_PATTERNS:
            m = re.search(pattern, q)
            if m:
                raw_size = m.group(1).lower()
                if stype in ('named', 'named_bare'):
                    size = self._SIZE_NORMALIZE.get(raw_size, raw_size.upper())
                elif stype == 'numeric':
                    size = raw_size  # keep as string "10", "12", etc.
                elif stype == 'eu':
                    size = f"EU {raw_size}"
                vibe = vibe[:m.start()] + vibe[m.end():]
                break

        # Exclusions ("not floral", "without black", "no heels")
        exclusions = []
        spans_to_remove = []
        for exc_pattern in self.EXCLUSION_PATTERNS:
            for m in re.finditer(exc_pattern, q):
                excluded_term = m.group(1).strip()
                if excluded_term and excluded_term not in exclusions:
                    exclusions.append(excluded_term)
                    spans_to_remove.append((m.start(), m.end()))
        # Remove exclusion spans from vibe in reverse order to preserve positions
        for start, end in sorted(spans_to_remove, reverse=True):
            vibe = vibe[:start] + vibe[end:]

        # Resolve material+exclusion conflict: if user says "no cotton",
        # cotton is excluded, not desired as a material filter
        if material and material.lower() in [e.lower() for e in exclusions]:
            material = None

        # Clean vibe text
        vibe = re.sub(r'[£$€]\s*\d+', '', vibe)
        vibe = re.sub(r'\b(under|below|over|above|less than|more than|up to)\b', '', vibe)
        vibe = re.sub(r'\s+', ' ', vibe).strip()
        if not vibe:
            vibe = raw

        return ParsedQuery(
            raw_query=raw, vibe_text=vibe,
            category_filter=category, color_filter=color,
            gender_filter=gender, price_min=price_min, price_max=price_max,
            style_tags=tags, material_filter=material,
            size_filter=size, exclusions=exclusions,
        )
