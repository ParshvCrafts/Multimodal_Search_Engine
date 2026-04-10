"""
engine/nlp.py — Multilingual query handling and spell correction.

Extracted from finalized_search_engine_full_script.py (lines 80-364).
Contains:
  - MultilingualHandler: language detection + dictionary-based translation
  - SpellCorrector: Norvig-style spell correction built from the product catalog
"""

import re
import logging
from typing import List, Tuple, Set
from collections import Counter

__all__ = ["MultilingualHandler", "SpellCorrector"]

logger = logging.getLogger("asos_search")


# ═══════════════════════════════════════════════════════════════════════════════
# MULTILINGUAL SUPPORT — lightweight language detection + translation
# ═══════════════════════════════════════════════════════════════════════════════
class MultilingualHandler:
    """
    Detects non-English queries and translates them to English using a
    dictionary-based approach for common fashion terms in major languages.
    For production, swap this with a proper translation API (Google Translate,
    DeepL, or a local model like Helsinki-NLP/opus-mt-*).
    """

    # Common fashion terms in multiple languages → English
    FASHION_DICT = {
        # French
        'robe': 'dress', 'jupe': 'skirt', 'chemise': 'shirt', 'pantalon': 'trousers',
        'veste': 'jacket', 'manteau': 'coat', 'chaussures': 'shoes',
        'bottes': 'boots', 'sac': 'bag', 'ceinture': 'belt',
        'rouge': 'red', 'bleu': 'blue', 'noir': 'black', 'blanc': 'white',
        'vert': 'green', 'jaune': 'yellow', 'rose': 'pink', 'gris': 'grey',
        'violet': 'purple', 'marron': 'brown', 'orange': 'orange',
        'élégant': 'elegant', 'décontracté': 'casual', 'chic': 'chic',
        'femme': 'women', 'homme': 'men', 'fille': 'girl',
        'soie': 'silk', 'coton': 'cotton', 'cuir': 'leather', 'lin': 'linen',
        'floral': 'floral', 'rayé': 'striped', 'imprimé': 'printed',
        'été': 'summer', 'hiver': 'winter', 'printemps': 'spring', 'automne': 'autumn',
        'mini': 'mini', 'maxi': 'maxi', 'midi': 'midi',
        'pas cher': 'budget', 'luxe': 'luxury', 'bon marché': 'cheap',

        # Spanish
        'vestido': 'dress', 'falda': 'skirt', 'camisa': 'shirt',
        'pantalón': 'trousers', 'pantalones': 'trousers', 'chaqueta': 'jacket',
        'abrigo': 'coat', 'zapatos': 'shoes', 'botas': 'boots',
        'bolso': 'bag', 'cinturón': 'belt', 'sombrero': 'hat',
        'rojo': 'red', 'azul': 'blue', 'negro': 'black', 'blanco': 'white',
        'verde': 'green', 'amarillo': 'yellow', 'rosado': 'pink', 'morado': 'purple',
        'marrón': 'brown', 'gris': 'grey', 'naranja': 'orange',
        'elegante': 'elegant', 'informal': 'casual', 'moderno': 'modern',
        'mujer': 'women', 'hombre': 'men', 'barato': 'cheap',
        'algodón': 'cotton', 'seda': 'silk', 'cuero': 'leather',
        'verano': 'summer', 'invierno': 'winter',

        # German
        'kleid': 'dress', 'rock': 'skirt', 'hemd': 'shirt', 'bluse': 'blouse',
        'hose': 'trousers', 'jacke': 'jacket', 'mantel': 'coat',
        'schuhe': 'shoes', 'stiefel': 'boots', 'tasche': 'bag',
        'gürtel': 'belt', 'hut': 'hat', 'pullover': 'sweater',
        'rot': 'red', 'blau': 'blue', 'schwarz': 'black', 'weiß': 'white',
        'weiss': 'white', 'grün': 'green', 'gelb': 'yellow', 'rosa': 'pink',
        'lila': 'purple', 'braun': 'brown', 'grau': 'grey',
        'frau': 'women', 'herren': 'men', 'damen': 'women',
        'seide': 'silk', 'baumwolle': 'cotton', 'leder': 'leather',
        'sommer': 'summer', 'winter': 'winter',

        # Italian
        'abito': 'dress', 'gonna': 'skirt', 'camicia': 'shirt',
        'giacca': 'jacket', 'cappotto': 'coat', 'scarpe': 'shoes',
        'stivali': 'boots', 'borsa': 'bag', 'cintura': 'belt',
        'rosso': 'red', 'blu': 'blue', 'nero': 'black', 'bianco': 'white',
        'grigio': 'grey', 'giallo': 'yellow', 'donna': 'women', 'uomo': 'men',
        'seta': 'silk', 'cotone': 'cotton', 'pelle': 'leather',
        'estate': 'summer', 'inverno': 'winter',

        # Portuguese
        'vestido': 'dress', 'saia': 'skirt', 'calça': 'trousers',
        'jaqueta': 'jacket', 'casaco': 'coat', 'sapatos': 'shoes',
        'bolsa': 'bag', 'vermelho': 'red', 'preto': 'black', 'branco': 'white',
        'mulher': 'women', 'homem': 'men',

        # Japanese (romaji)
        'doresu': 'dress', 'sukato': 'skirt', 'shatsu': 'shirt',
        'zubon': 'trousers', 'jaketto': 'jacket', 'kutsu': 'shoes',
        'baggu': 'bag', 'aka': 'red', 'ao': 'blue', 'kuro': 'black',
        'shiro': 'white',

        # Common multilingual fashion terms
        'kimono': 'kimono', 'sari': 'sari', 'hijab': 'hijab',
        'kaftan': 'kaftan', 'poncho': 'poncho',
    }

    # Character-range heuristics for script detection
    _LATIN_EXTENDED = re.compile(r'[àáâãäåæçèéêëìíîïðñòóôõöùúûüýþÿ]', re.I)
    _CJK = re.compile(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]')
    _CYRILLIC = re.compile(r'[\u0400-\u04ff]')
    _ARABIC = re.compile(r'[\u0600-\u06ff]')
    _DEVANAGARI = re.compile(r'[\u0900-\u097f]')

    @classmethod
    def detect_language(cls, text: str) -> str:
        """Return a rough language tag: 'en', 'fr', 'es', 'de', 'it', 'pt', 'ja', 'zh', 'ar', 'hi', 'ru', or 'other'."""
        if cls._CJK.search(text):
            return 'ja' if re.search(r'[\u3040-\u30ff]', text) else 'zh'
        if cls._CYRILLIC.search(text):
            return 'ru'
        if cls._ARABIC.search(text):
            return 'ar'
        if cls._DEVANAGARI.search(text):
            return 'hi'

        words = set(re.findall(r'\b[a-zàáâãäåæçèéêëìíîïñòóôõöùúûüýÿ]+\b', text.lower()))
        # French markers
        fr_markers = {'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'en', 'pour', 'avec', 'je', 'ce', 'cette'}
        es_markers = {'el', 'la', 'los', 'las', 'un', 'una', 'de', 'en', 'y', 'para', 'con', 'por', 'que', 'muy'}
        de_markers = {'der', 'die', 'das', 'ein', 'eine', 'und', 'für', 'mit', 'ich', 'ist', 'nicht', 'auch'}
        it_markers = {'il', 'lo', 'la', 'gli', 'le', 'un', 'una', 'di', 'e', 'per', 'con', 'che', 'sono'}
        pt_markers = {'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'em', 'para', 'com', 'que', 'não'}

        scores = {
            'fr': len(words & fr_markers),
            'es': len(words & es_markers),
            'de': len(words & de_markers),
            'it': len(words & it_markers),
            'pt': len(words & pt_markers),
        }
        best = max(scores, key=scores.get)
        if scores[best] >= 2:
            return best

        # Check if any words are in our fashion dictionary
        dict_words = words & set(cls.FASHION_DICT.keys())
        en_words = {'the', 'a', 'an', 'in', 'on', 'for', 'with', 'and', 'or', 'is', 'are'}
        if dict_words and not (words & en_words):
            return 'other'

        return 'en'

    @classmethod
    def translate_query(cls, query: str) -> Tuple[str, str, bool]:
        """
        Translate a query to English using the fashion dictionary.

        Returns: (translated_query, detected_language, was_translated)
        """
        lang = cls.detect_language(query)

        if lang == 'en':
            return query, 'en', False

        # For non-Latin scripts, we can't do dictionary translation
        if lang in ('ja', 'zh', 'ar', 'hi', 'ru'):
            logger.info(f"Non-Latin script detected ({lang}). Passing through to CLIP.")
            return query, lang, False

        # Dictionary-based word-by-word translation for Latin-script languages
        words = query.lower().split()
        translated = []
        was_translated = False

        i = 0
        while i < len(words):
            # Try 2-word phrases first
            if i + 1 < len(words):
                bigram = f"{words[i]} {words[i+1]}"
                if bigram in cls.FASHION_DICT:
                    translated.append(cls.FASHION_DICT[bigram])
                    was_translated = True
                    i += 2
                    continue

            word = words[i]
            if word in cls.FASHION_DICT:
                translated.append(cls.FASHION_DICT[word])
                was_translated = True
            else:
                translated.append(word)
            i += 1

        result = ' '.join(translated)
        if was_translated:
            logger.info(f"Translated [{lang}]: \"{query}\" → \"{result}\"")

        return result, lang, was_translated


# ═══════════════════════════════════════════════════════════════════════════════
# QUERY SPELL-CORRECTION
# ═══════════════════════════════════════════════════════════════════════════════
class SpellCorrector:
    """
    Lightweight spell correction for fashion search queries.
    Uses a vocabulary built from the product catalog + common fashion terms.
    Based on Peter Norvig's spell corrector algorithm.
    """

    def __init__(self):
        self.word_freq: Counter = Counter()
        self._ready = False

    def fit(self, texts: List[str]):
        """Build vocabulary from product catalog texts."""
        for text in texts:
            words = re.findall(r'\b[a-z]+\b', str(text).lower())
            self.word_freq.update(words)

        # Boost common fashion terms
        fashion_boost = [
            'dress', 'dresses', 'skirt', 'shirt', 'blouse', 'jacket', 'coat',
            'jeans', 'trousers', 'shorts', 'hoodie', 'sweater', 'cardigan',
            'boots', 'sneakers', 'trainers', 'sandals', 'heels', 'shoes',
            'bag', 'handbag', 'tote', 'backpack', 'clutch',
            'black', 'white', 'blue', 'red', 'green', 'pink', 'yellow',
            'purple', 'brown', 'grey', 'gray', 'navy', 'beige', 'cream',
            'casual', 'formal', 'elegant', 'vintage', 'boho', 'minimalist',
            'streetwear', 'oversized', 'cropped', 'fitted', 'floral',
            'leather', 'denim', 'satin', 'silk', 'cotton', 'linen',
            'summer', 'winter', 'spring', 'autumn', 'party', 'office',
            'midi', 'mini', 'maxi', 'sequin', 'lace', 'velvet',
        ]
        for w in fashion_boost:
            self.word_freq[w] += 1000

        self._ready = True
        logger.info(f"SpellCorrector fitted with {len(self.word_freq):,} words")

    def _edits1(self, word: str) -> Set[str]:
        """All edits that are one edit distance away from `word`."""
        letters = 'abcdefghijklmnopqrstuvwxyz'
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        deletes = [L + R[1:] for L, R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
        replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
        inserts = [L + c + R for L, R in splits for c in letters]
        return set(deletes + transposes + replaces + inserts)

    def _edits2(self, word: str) -> Set[str]:
        """All edits that are two edits away from `word`."""
        return set(e2 for e1 in self._edits1(word) for e2 in self._edits1(e1))

    def _known(self, words: Set[str]) -> Set[str]:
        """Subset of words that are in the vocabulary."""
        return words & set(self.word_freq.keys())

    def correct_word(self, word: str) -> str:
        """Return the most likely spelling correction for a single word."""
        if not self._ready or len(word) <= 2:
            return word

        word_lower = word.lower()

        # Already known
        if word_lower in self.word_freq:
            return word

        # Edit distance 1
        candidates = self._known(self._edits1(word_lower))
        if candidates:
            best = max(candidates, key=self.word_freq.get)
            if self.word_freq[best] > 10:  # Only correct if the candidate is common enough
                return best

        # Edit distance 2 (only for longer words)
        if len(word_lower) >= 5:
            candidates = self._known(self._edits2(word_lower))
            if candidates:
                best = max(candidates, key=self.word_freq.get)
                if self.word_freq[best] > 50:
                    return best

        return word

    def correct_query(self, query: str) -> Tuple[str, bool]:
        """
        Correct a full query string.
        Returns: (corrected_query, was_corrected)
        """
        if not self._ready:
            return query, False

        words = query.split()
        corrected = []
        was_corrected = False

        for word in words:
            # Don't correct price tokens, numbers, or currency symbols
            if re.match(r'^[£$€]?\d', word) or len(word) <= 2:
                corrected.append(word)
                continue

            fixed = self.correct_word(word)
            if fixed != word:
                was_corrected = True
                corrected.append(fixed)
            else:
                corrected.append(word)

        result = ' '.join(corrected)
        if was_corrected:
            logger.info(f"Spell-corrected: \"{query}\" → \"{result}\"")
        return result, was_corrected
