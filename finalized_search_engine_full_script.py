import os, shutil, json
from pathlib import Path

PERSISTENT_DIR = os.path.join(".", "asos_engine")
DATA_PATH = "./asos_clean.csv"  # or .parquet
EPHEMERAL_CACHE = "./asos_image_cache"

# Create directories
os.makedirs(PERSISTENT_DIR, exist_ok=True)
os.makedirs(EPHEMERAL_CACHE, exist_ok=True)

# Auto-detect parquet vs csv
if not os.path.exists(DATA_PATH):
    alt = DATA_PATH.replace('.csv', '.parquet')
    if os.path.exists(alt):
        DATA_PATH = alt


# ═══════════════════════════════════════════════════════════════════════════════
# ASOS SEARCH ENGINE v3.3 — MULTIMODAL + MULTILINGUAL
# ═══════════════════════════════════════════════════════════════════════════════
# All classes: SearchConfig, FashionCLIPEncoder, DualFAISSIndex,
# QueryParser, SimpleBM25, ASOSSearchEngine, SearchEvaluator, display_results.

# ═══════════════════════════════════════════════════════════════════════════════

import os
import io
import re
import ast
import gc
import sys
import json
import time
import math
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union, Set
from dataclasses import dataclass, field
from collections import Counter

import numpy as np
import pandas as pd

import torch
import torch.nn.functional as F
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

import faiss
from tqdm.auto import tqdm

import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-7s | %(name)s | %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger("asos_search")

for _noisy in ("urllib3", "urllib3.connectionpool", "requests", "PIL",
               "transformers", "transformers.modeling_utils"):
    logging.getLogger(_noisy).setLevel(logging.ERROR)


def _detect_environment() -> str:
    if 'google.colab' in sys.modules:
        return 'colab'
    if 'KAGGLE_KERNEL_RUN_TYPE' in os.environ:
        return 'kaggle'
    return 'local'


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


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
@dataclass
class SearchConfig:
    """Central configuration — v3.1 with multilingual + spell correction."""

    # ── Model ──
    primary_model: str = "patrickjohncyh/fashion-clip"
    fallback_model: str = "openai/clip-vit-base-patch32"
    embedding_dim: int = 512
    device: str = ""
    hf_token: Optional[str] = None

    # ── FAISS Index ──
    n_clusters: int = 256
    n_probe: int = 20

    # ── Search Pipeline ──
    retrieval_top_k: int = 300
    final_top_n: int = 20

    # ── Dual-Index Fusion ──
    rrf_k: int = 60
    image_index_weight: float = 0.55
    text_index_weight: float = 0.45

    # ── Re-ranking Weights ──
    alpha_clip: float = 0.55
    beta_tags: float = 0.25
    gamma_text: float = 0.15
    delta_freshness: float = 0.05

    # ── CLIP Prompt Ensembling ──
    prompt_templates: Tuple[str, ...] = (
        "a photo of {}, a fashion product",
        "a product photo of {}",
        "a fashion item: {}",
        "{}, studio product photography",
        "an e-commerce photo of {}",
    )

    # ── Embedding Computation ──
    embed_batch_size: int = 32
    embed_checkpoint_interval: int = 2000

    # ── Features ──
    enable_multilingual: bool = True
    enable_spell_correction: bool = True

    # ── Paths (auto-detected) ──
    data_dir: str = ""
    data_path: str = ""
    persistent_dir: str = ""
    image_cache_dir: str = ""

    # ── Derived Paths ──
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

        if env == 'colab':
            drive_base = "/content/drive/MyDrive/Colab Notebooks"
            if not self.data_dir:
                self.data_dir = drive_base
            if not self.persistent_dir:
                self.persistent_dir = os.path.join(drive_base, "asos_engine")
            if not self.image_cache_dir:
                self.image_cache_dir = "/content/asos_image_cache"
        elif env == 'kaggle':
            if not self.data_dir:
                self.data_dir = "/kaggle/input"
            if not self.persistent_dir:
                self.persistent_dir = "/kaggle/working/asos_engine"
            if not self.image_cache_dir:
                self.image_cache_dir = "/kaggle/working/asos_image_cache"
        else:
            if not self.data_dir:
                self.data_dir = "."
            if not self.persistent_dir:
                self.persistent_dir = "./asos_engine"
            if not self.image_cache_dir:
                self.image_cache_dir = "./asos_image_cache"

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


# ═══════════════════════════════════════════════════════════════════════════════
# FASHION CLIP ENCODER
# ═══════════════════════════════════════════════════════════════════════════════
class FashionCLIPEncoder:
    """
    v3.1 — Handles models that return BaseModelOutputWithPooling
    instead of raw tensors from get_text_features / get_image_features.
    """

    def __init__(self, config: SearchConfig):
        self.config = config
        self.device = config.device
        self.model = None
        self.processor = None
        self.model_name = None
        self._load_model()

    def _load_model(self):
        models_to_try = [self.config.primary_model, self.config.fallback_model]
        for model_name in models_to_try:
            try:
                logger.info(f"Loading model: {model_name}")
                kwargs = {}
                if self.config.hf_token:
                    kwargs['token'] = self.config.hf_token
                self.model = CLIPModel.from_pretrained(model_name, **kwargs)
                self.processor = CLIPProcessor.from_pretrained(model_name, **kwargs)
                self.model = self.model.to(self.device)
                self.model.eval()
                self.model_name = model_name

                # ── Probe the model to find actual embedding dim ──
                test_inputs = self.processor(
                    text=["test"], return_tensors="pt",
                    padding=True, truncation=True, max_length=77,
                )
                test_inputs = {k: v.to(self.device) for k, v in test_inputs.items()}
                with torch.no_grad():
                    test_out = self.model.get_text_features(**test_inputs)
                    test_tensor = self._to_tensor(test_out)
                actual_dim = test_tensor.shape[-1]
                if actual_dim != self.config.embedding_dim:
                    logger.info(
                        f"Model embedding dim = {actual_dim} "
                        f"(config said {self.config.embedding_dim}). Updating config."
                    )
                    self.config.embedding_dim = actual_dim

                logger.info(f"Model loaded: {model_name} on {self.device} (dim={actual_dim})")
                return
            except Exception as e:
                logger.warning(f"Failed to load {model_name}: {e}")
                continue
        raise RuntimeError(
            "Could not load any CLIP model. Check internet connection and HF_TOKEN."
        )

    @staticmethod
    def _to_tensor(output) -> torch.Tensor:
        if isinstance(output, torch.Tensor):
            return output
        if hasattr(output, 'pooler_output') and output.pooler_output is not None:
            return output.pooler_output
        if hasattr(output, 'last_hidden_state'):
            return output.last_hidden_state.mean(dim=1)
        if hasattr(output, 'text_embeds'):
            return output.text_embeds
        if hasattr(output, 'image_embeds'):
            return output.image_embeds
        if isinstance(output, (tuple, list)) and len(output) > 0:
            return output[0] if isinstance(output[0], torch.Tensor) else output[1]
        raise TypeError(
            f"Cannot extract tensor from model output of type {type(output)}. "
            f"Available attributes: {[a for a in dir(output) if not a.startswith('_')]}"
        )

    @torch.no_grad()
    def encode_texts(self, texts: List[str], batch_size: Optional[int] = None) -> np.ndarray:
        batch_size = batch_size or min(self.config.embed_batch_size * 4, 256)
        texts = [str(t) if t and str(t) != 'nan' else '' for t in texts]
        all_emb = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            inputs = self.processor(
                text=batch, return_tensors="pt",
                padding=True, truncation=True, max_length=77,
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            raw = self.model.get_text_features(**inputs)
            feats = self._to_tensor(raw)
            feats = F.normalize(feats, p=2, dim=-1).cpu().numpy()
            all_emb.append(feats)
        return np.vstack(all_emb).astype(np.float32)

    @torch.no_grad()
    def encode_images_from_paths(
        self, paths: List[Path], batch_size: Optional[int] = None,
    ) -> np.ndarray:
        batch_size = batch_size or self.config.embed_batch_size
        n = len(paths)
        dim = self.config.embedding_dim
        embeddings = np.zeros((n, dim), dtype=np.float32)

        for start in range(0, n, batch_size):
            end = min(start + batch_size, n)
            batch_paths = paths[start:end]

            images = []
            valid_in_batch = []
            for j, p in enumerate(batch_paths):
                try:
                    img = Image.open(p).convert("RGB")
                    images.append(img)
                    valid_in_batch.append(start + j)
                except Exception:
                    pass

            if not images:
                continue

            try:
                inputs = self.processor(images=images, return_tensors="pt", padding=True)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                if self.device == "cuda":
                    with torch.amp.autocast("cuda"):
                        raw = self.model.get_image_features(**inputs)
                else:
                    raw = self.model.get_image_features(**inputs)
                feats = self._to_tensor(raw)
                feats = F.normalize(feats, p=2, dim=-1).cpu().numpy()
                for local_j, global_j in enumerate(valid_in_batch):
                    embeddings[global_j] = feats[local_j]
            except Exception as e:
                logger.warning(f"Batch encoding failed at {start}: {e}")

            if self.device == "cuda" and start % (batch_size * 10) == 0:
                torch.cuda.empty_cache()

        return embeddings

    @torch.no_grad()
    def encode_images(self, images: List[Image.Image], batch_size: Optional[int] = None) -> np.ndarray:
        batch_size = batch_size or self.config.embed_batch_size
        all_emb = []
        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            inputs = self.processor(images=batch, return_tensors="pt", padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            if self.device == "cuda":
                with torch.amp.autocast("cuda"):
                    raw = self.model.get_image_features(**inputs)
            else:
                raw = self.model.get_image_features(**inputs)
            feats = self._to_tensor(raw)
            all_emb.append(F.normalize(feats, p=2, dim=-1).cpu().numpy())
        return np.vstack(all_emb).astype(np.float32)

    @torch.no_grad()
    def encode_query_text(self, query: str) -> np.ndarray:
        prompted = [tmpl.format(query) for tmpl in self.config.prompt_templates]
        embeddings = self.encode_texts(prompted)
        avg = embeddings.mean(axis=0, keepdims=True)
        avg = avg / (np.linalg.norm(avg, axis=-1, keepdims=True) + 1e-8)
        return avg.astype(np.float32)

    @torch.no_grad()
    def encode_multimodal_query(
        self, text: str, image: Image.Image, text_weight: float = 0.5,
    ) -> np.ndarray:
        text_emb = self.encode_query_text(text)
        img_emb = self.encode_images([image])
        fused = text_weight * text_emb + (1 - text_weight) * img_emb
        fused = fused / (np.linalg.norm(fused, axis=-1, keepdims=True) + 1e-8)
        return fused.astype(np.float32)


# ═══════════════════════════════════════════════════════════════════════════════
# FAISS DUAL-INDEX MANAGER
# ═══════════════════════════════════════════════════════════════════════════════
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


# ═══════════════════════════════════════════════════════════════════════════════
# QUERY PARSER (NLU)
# ═══════════════════════════════════════════════════════════════════════════════
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


# ═══════════════════════════════════════════════════════════════════════════════
# BM25
# ═══════════════════════════════════════════════════════════════════════════════
class SimpleBM25:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_tokens: List[List[str]] = []
        self.avg_dl: float = 0
        self.df: Dict[str, int] = {}
        self.n_docs: int = 0

    def fit(self, documents: List[str]):
        self.doc_tokens = [self._tokenize(d) for d in documents]
        self.n_docs = len(self.doc_tokens)
        self.avg_dl = np.mean([len(t) for t in self.doc_tokens]) if self.doc_tokens else 1
        self.df = Counter()
        for tokens in self.doc_tokens:
            for t in set(tokens):
                self.df[t] += 1

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\b[a-z]+\b', str(text).lower())

    def score_candidates(self, query: str, candidate_indices: List[int]) -> np.ndarray:
        q_tokens = self._tokenize(query)
        scores = np.zeros(len(candidate_indices), dtype=np.float32)
        for i, doc_idx in enumerate(candidate_indices):
            if doc_idx >= len(self.doc_tokens):
                continue
            doc = self.doc_tokens[doc_idx]
            dl = len(doc)
            tf_doc = Counter(doc)
            s = 0.0
            for qt in q_tokens:
                if qt not in self.df:
                    continue
                tf = tf_doc.get(qt, 0)
                idf = np.log((self.n_docs - self.df[qt] + 0.5) / (self.df[qt] + 0.5) + 1)
                num = tf * (self.k1 + 1)
                den = tf + self.k1 * (1 - self.b + self.b * dl / self.avg_dl)
                s += idf * num / den
            scores[i] = s
        return scores


# ═══════════════════════════════════════════════════════════════════════════════
# ASOS SEARCH ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
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

    # ── Search ──

    def search(
        self, query: str,
        query_image: Optional[Image.Image] = None,
        top_n: Optional[int] = None,
        text_weight: float = 0.5,
        sort_by: str = 'relevance',
    ) -> pd.DataFrame:
        if not self._is_ready:
            raise RuntimeError("Engine not ready. Call build_index() first.")
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
        filtered = self._apply_filters(candidates, parsed)
        if len(filtered) == 0:
            logger.warning("Zero results after filtering. Relaxing constraints...")
            filtered = self._relax_and_retry(candidates, parsed, min_results=top_n)

        # Hybrid re-ranking
        ranked = self._hybrid_rerank(filtered, parsed)

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
        suggested_searches = self._generate_suggestions(results, parsed)

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
            raise RuntimeError("Engine not ready.")

        # ── FIX: compare as strings consistently ──
        sku_str = str(sku)
        match = self.metadata[self.metadata['sku'] == sku_str]
        if len(match) == 0:
            raise ValueError(f"SKU '{sku_str}' not found in metadata ({self.metadata['sku'].dtype})")

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
            raise RuntimeError("Engine not ready.")

        sku_str = str(sku)
        match = self.metadata[self.metadata['sku'] == sku_str]
        if len(match) == 0:
            raise ValueError(f"SKU '{sku_str}' not found")

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

    # ── Suggested Searches — auto-generate related query refinements ──

    def _generate_suggestions(self, results: pd.DataFrame, parsed: ParsedQuery,
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

    # ── Internal: Filtering ──

    def _apply_filters(self, candidates: pd.DataFrame, parsed: ParsedQuery) -> pd.DataFrame:
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

    def _relax_and_retry(self, candidates: pd.DataFrame, parsed: ParsedQuery,
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
                result = self._apply_filters(candidates, relaxed)
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
            result = self._apply_filters(candidates, relaxed)
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
                result = self._apply_filters(candidates, relaxed)
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
                result = self._apply_filters(candidates, relaxed)
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
            result = self._apply_filters(candidates, relaxed)
            if len(result) > len(best_so_far):
                best_so_far = result
            if len(result) >= min_results:
                logger.info(f"Dropped price_max entirely -> {len(result)} results")
                return result

        if parsed.price_min is not None:
            relaxed.price_min = None
            result = self._apply_filters(candidates, relaxed)
            if len(result) > len(best_so_far):
                best_so_far = result
            if len(result) >= min_results:
                logger.info(f"Dropped price_min -> {len(result)} results")
                return result

        # Phase 3: Drop category as last resort
        if relaxed.category_filter is not None:
            relaxed.category_filter = None
            result = self._apply_filters(candidates, relaxed)
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

    # ── Internal: Hybrid Re-ranking ──

    def _hybrid_rerank(self, candidates: pd.DataFrame, parsed: ParsedQuery) -> pd.DataFrame:
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
        if self.bm25 is not None and '_orig_idx' in scored.columns:
            bm25_raw = self.bm25.score_candidates(parsed.raw_query, scored['_orig_idx'].tolist())
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
                self.config.alpha_clip * scored['rrf_norm'] +
                self.config.beta_tags * scored['tag_score'] +
                self.config.gamma_text * scored['bm25_norm'] +
                self.config.delta_freshness * scored['stock_bonus']
            )
        return scored.sort_values('hybrid_score', ascending=False)


# ═══════════════════════════════════════════════════════════════════════════════
# EVALUATION
# ═══════════════════════════════════════════════════════════════════════════════
@dataclass
class EvalResult:
    query: str
    recall_at_k: Dict[int, float]
    precision_at_k: Dict[int, float]
    mrr: float
    latency_ms: float


class SearchEvaluator:
    def __init__(self, engine: ASOSSearchEngine):
        self.engine = engine

    def evaluate_single(self, query: str, relevant_skus: Set[str],
                        k_values: List[int] = [5, 10, 20]) -> EvalResult:
        max_k = max(k_values)
        t0 = time.time()
        results = self.engine.search(query, top_n=max_k)
        latency = (time.time() - t0) * 1000

        retrieved = results['sku'].astype(str).tolist()
        relevant = set(str(s) for s in relevant_skus)

        recall_at, precision_at = {}, {}
        for k in k_values:
            top_k = retrieved[:k]
            found = len(set(top_k) & relevant)
            recall_at[k] = found / len(relevant) if relevant else 0.0
            precision_at[k] = found / k if k > 0 else 0.0

        mrr = 0.0
        for rank, sku in enumerate(retrieved, 1):
            if sku in relevant:
                mrr = 1.0 / rank
                break

        return EvalResult(query=query, recall_at_k=recall_at,
                          precision_at_k=precision_at, mrr=mrr, latency_ms=latency)

    def evaluate(self, test_queries: List[Dict],
                 k_values: List[int] = [5, 10, 20]) -> Dict:
        results = []
        for tq in tqdm(test_queries, desc="Evaluating"):
            try:
                res = self.evaluate_single(
                    tq['query'],
                    set(str(s) for s in tq['relevant_skus']),
                    k_values,
                )
                results.append(res)
            except Exception as e:
                logger.warning(f"Eval failed for '{tq['query']}': {e}")

        if not results:
            return {"error": "No successful evaluations"}

        agg = {
            "n_queries": len(results),
            "avg_latency_ms": np.mean([r.latency_ms for r in results]),
            "median_latency_ms": np.median([r.latency_ms for r in results]),
            "mean_mrr": np.mean([r.mrr for r in results]),
        }
        for k in k_values:
            agg[f"mean_recall@{k}"] = np.mean([r.recall_at_k.get(k, 0) for r in results])
            agg[f"mean_precision@{k}"] = np.mean([r.precision_at_k.get(k, 0) for r in results])

        return {"aggregate": agg, "per_query": results}

    @staticmethod
    def print_report(report: Dict):
        agg = report.get("aggregate", {})
        print("\n" + "=" * 65)
        print("  SEARCH ENGINE EVALUATION REPORT")
        print("=" * 65)
        print(f"  Queries evaluated:   {agg.get('n_queries', 0)}")
        print(f"  Avg latency:         {agg.get('avg_latency_ms', 0):.1f} ms")
        print(f"  Mean MRR:            {agg.get('mean_mrr', 0):.4f}")
        for key, val in sorted(agg.items()):
            if 'recall' in key or 'precision' in key:
                print(f"  {key:25s}  {val:.4f}")
        print("=" * 65)


# ═══════════════════════════════════════════════════════════════════════════════
# DISPLAY UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════
def display_results(results: pd.DataFrame, max_display: int = 10, show_query_info: bool = True):
    """Render search results as a card grid in Jupyter/Colab."""
    try:
        from IPython.display import display, HTML
    except ImportError:
        for _, row in results.head(max_display).iterrows():
            print(f"  {row.get('name', '?')[:55]}  {row.get('price', 0):.2f}  "
                  f"{row.get('color_clean', '')}  {row.get('category', '')}")
        return

    # Show query info banner if available
    query_info = results.attrs.get('query_info', {})
    banner = ""
    if show_query_info and query_info:
        parts = []
        if query_info.get('was_translated'):
            parts.append(f"Translated from <b>{query_info['detected_language']}</b>: "
                        f"\"{query_info['original_query']}\" &rarr; \"{query_info['processed_query']}\"")
        if query_info.get('was_spell_corrected'):
            parts.append(f"Did you mean: <b>{query_info['spell_suggestion']}</b>?")

        # Show sort indicator
        sort_by = query_info.get('sort_by', 'relevance')
        if sort_by != 'relevance':
            sort_labels = {'price_asc': 'Price: Low to High', 'price_desc': 'Price: High to Low',
                           'name_asc': 'Name: A-Z', 'name_desc': 'Name: Z-A'}
            parts.append(f"Sorted by: <b>{sort_labels.get(sort_by, sort_by)}</b>")

        # Show active filters (v3.3)
        active = []
        if query_info.get('parsed_material'):
            active.append(f"Material: <b>{query_info['parsed_material']}</b>")
        if query_info.get('parsed_size'):
            active.append(f"Size: <b>{query_info['parsed_size']}</b>")
        if query_info.get('parsed_exclusions'):
            excl_str = ', '.join(query_info['parsed_exclusions'])
            active.append(f"Excluding: <b>{excl_str}</b>")
        if active:
            parts.append(' | '.join(active))

        # Show suggested searches
        suggestions = query_info.get('suggested_searches', [])
        if suggestions:
            pills = ' '.join(
                f'<span style="display:inline-block;padding:2px 8px;margin:2px;'
                f'background:#e8f0fe;border-radius:12px;font-size:11px;color:#1a56db;">{s}</span>'
                for s in suggestions[:4]
            )
            parts.append(f"Related: {pills}")

        if parts:
            banner = (
                '<div style="padding:8px 12px;margin-bottom:8px;background:#f0f7ff;'
                'border-left:3px solid #2563eb;border-radius:4px;font-family:system-ui;font-size:12px;">'
                + '<br>'.join(parts) + '</div>'
            )

    cards = []
    for _, row in results.head(max_display).iterrows():
        img = row.get('primary_image_url', '')
        name = str(row.get('name', 'N/A'))[:48]
        price = row.get('price', 0)
        brand = row.get('brand', '')
        cat = row.get('category', '')
        color = row.get('color_clean', '')
        score = row.get('hybrid_score', row.get('rrf_score', row.get('score', 0)))
        tags = row.get('style_tags', [])
        tag_str = ', '.join(tags[:3]) if isinstance(tags, list) else ''
        sku = row.get('sku', '')

        card = f'''
        <div style="width:190px;border:1px solid #e0e0e0;border-radius:10px;
                    padding:8px;background:#fff;font-family:system-ui,sans-serif;
                    box-shadow:0 2px 8px rgba(0,0,0,0.06);cursor:pointer;"
             title="SKU: {sku} | Click for details">
            <img src="{img}" style="width:100%;height:240px;object-fit:cover;
                 border-radius:6px;background:#f5f5f5;"
                 onerror="this.style.display='none'"/>
            <p style="margin:6px 0 2px;font-weight:600;font-size:11px;
                      line-height:1.3;height:28px;overflow:hidden;">{name}</p>
            <p style="margin:0;font-size:10px;color:#888;">{brand} | {cat}</p>
            <p style="margin:3px 0;font-size:14px;font-weight:700;
                      color:#1a7a3a;">&pound;{price:.2f}</p>
            <p style="margin:0;font-size:9px;color:#aaa;">{color} | score {score:.3f}</p>
            {"<p style='margin:2px 0 0;font-size:9px;color:#c06;'>"+tag_str+"</p>" if tag_str else ""}
        </div>'''
        cards.append(card)

    html = banner + (
        '<div style="display:flex;flex-wrap:wrap;gap:12px;padding:8px;">'
        + ''.join(cards) + '</div>'
    )
    display(HTML(html))


def display_product_detail(engine: 'ASOSSearchEngine', sku):
    """Display full product detail page for a single SKU."""
    try:
        from IPython.display import display, HTML
    except ImportError:
        print("IPython not available for rich display.")
        return

    detail = engine.get_product_detail(sku)
    if detail is None:
        print(f"SKU {sku} not found.")
        return

    name = detail.get('name', 'N/A')
    price = detail.get('price', 0)
    brand = detail.get('brand', '')
    cat = detail.get('category', '')
    color = detail.get('color_clean', '')
    gender = detail.get('gender', '')
    details_text = detail.get('product_details', '')
    materials = detail.get('materials', [])
    sizes = detail.get('sizes_available', [])
    tags = detail.get('style_tags', [])
    image_urls = detail.get('image_urls', [detail.get('primary_image_url', '')])

    images_html = ''.join(
        f'<img src="{url}" style="width:200px;height:260px;object-fit:cover;'
        f'border-radius:8px;background:#f5f5f5;" onerror="this.style.display=\'none\'"/>'
        for url in image_urls[:6]
    )

    mat_str = ', '.join(materials) if isinstance(materials, list) else str(materials)
    sizes_str = ', '.join(sizes) if isinstance(sizes, list) else str(sizes)
    tags_str = ', '.join(tags) if isinstance(tags, list) else str(tags)

    html = f'''
    <div style="font-family:system-ui,sans-serif;max-width:800px;padding:16px;
                border:1px solid #e0e0e0;border-radius:12px;background:#fff;">
        <h2 style="margin:0 0 4px;">{name}</h2>
        <p style="color:#888;margin:0 0 12px;">{brand} | {cat} | {gender} | {color}</p>
        <div style="display:flex;gap:8px;overflow-x:auto;margin-bottom:16px;">
            {images_html}
        </div>
        <p style="font-size:24px;font-weight:700;color:#1a7a3a;margin:8px 0;">&pound;{price:.2f}</p>
        <table style="font-size:13px;border-collapse:collapse;width:100%;">
            <tr><td style="padding:4px 8px;font-weight:600;width:120px;">Materials</td><td>{mat_str}</td></tr>
            <tr><td style="padding:4px 8px;font-weight:600;">Sizes</td><td>{sizes_str}</td></tr>
            <tr><td style="padding:4px 8px;font-weight:600;">Style Tags</td><td>{tags_str}</td></tr>
            <tr><td style="padding:4px 8px;font-weight:600;">Details</td><td>{details_text}</td></tr>
        </table>
    </div>'''
    display(HTML(html))


def display_outfit(engine: 'ASOSSearchEngine', sku, n_per_category: int = 3):
    """Display 'Complete the Look' outfit recommendations for a product."""
    try:
        from IPython.display import display, HTML
    except ImportError:
        print("IPython not available.")
        return

    source = engine.get_product_detail(sku)
    if source is None:
        print(f"SKU {sku} not found.")
        return

    outfit = engine.complete_the_look(sku, n_per_category=n_per_category)

    # Source product header
    header = f'''
    <div style="font-family:system-ui,sans-serif;padding:12px;margin-bottom:8px;
                background:#f9fafb;border-radius:10px;border:2px solid #2563eb;">
        <div style="display:flex;gap:12px;align-items:center;">
            <img src="{source.get('primary_image_url', '')}"
                 style="width:80px;height:100px;object-fit:cover;border-radius:6px;"
                 onerror="this.style.display='none'"/>
            <div>
                <p style="margin:0;font-weight:700;font-size:14px;">Complete the Look</p>
                <p style="margin:2px 0;font-size:12px;color:#555;">{source.get('name', '')}</p>
                <p style="margin:0;font-size:13px;font-weight:600;color:#1a7a3a;">
                   &pound;{source.get('price', 0):.2f}</p>
            </div>
        </div>
    </div>'''

    sections = []
    for cat, items_df in outfit.items():
        cards = []
        for _, row in items_df.iterrows():
            card = f'''
            <div style="width:150px;border:1px solid #e0e0e0;border-radius:8px;
                        padding:6px;background:#fff;font-family:system-ui;">
                <img src="{row.get('primary_image_url', '')}"
                     style="width:100%;height:180px;object-fit:cover;border-radius:5px;"
                     onerror="this.style.display='none'"/>
                <p style="margin:4px 0 1px;font-weight:600;font-size:10px;
                          line-height:1.2;height:24px;overflow:hidden;">{str(row.get('name', ''))[:40]}</p>
                <p style="margin:0;font-size:12px;font-weight:700;color:#1a7a3a;">
                   &pound;{row.get('price', 0):.2f}</p>
                <p style="margin:0;font-size:9px;color:#aaa;">{row.get('brand', '')}</p>
            </div>'''
            cards.append(card)

        sections.append(f'''
        <div style="margin-bottom:12px;">
            <p style="font-family:system-ui;font-weight:600;font-size:12px;
                      color:#6b7280;margin:0 0 6px;">{cat}</p>
            <div style="display:flex;gap:8px;overflow-x:auto;">{''.join(cards)}</div>
        </div>''')

    html = header + ''.join(sections)
    display(HTML(html))


def sort_results(results: pd.DataFrame, sort_by: str) -> pd.DataFrame:
    """
    Re-sort an existing results DataFrame. Useful for frontend sort toggling
    without re-running the search.

    sort_by: 'relevance', 'price_asc', 'price_desc', 'name_asc', 'name_desc'
    """
    sort_options = {
        'relevance': ('hybrid_score', False),
        'price_asc': ('price', True),
        'price_desc': ('price', False),
        'name_asc': ('name', True),
        'name_desc': ('name', False),
    }
    if sort_by not in sort_options:
        raise ValueError(f"Unknown sort: {sort_by}. Options: {list(sort_options.keys())}")

    col, ascending = sort_options[sort_by]
    if col not in results.columns:
        return results

    sorted_df = results.sort_values(col, ascending=ascending).reset_index(drop=True)
    sorted_df.index = range(1, len(sorted_df) + 1)
    sorted_df.index.name = 'rank'

    # Preserve attrs
    if hasattr(results, 'attrs'):
        sorted_df.attrs = results.attrs.copy()
        if 'query_info' in sorted_df.attrs:
            sorted_df.attrs['query_info']['sort_by'] = sort_by

    return sorted_df


print("Engine classes defined (v3.2 — sort + price proximity + Complete the Look + suggestions)")


config = SearchConfig()

engine = ASOSSearchEngine(config)
engine.load_data()
engine.build_index()
print(f"\n✅ Engine ready with {len(engine.metadata):,} products indexed")

# ── Text-only search demos ──
demo_queries = [
    "coastal summer cardigan under £50",
    "Y2K cyber party look",
    "black leather jacket edgy streetwear",
    "floral midi dress for women romantic under £40",
    "oversized hoodie men's casual",
    "minimalist white trainers",
    "boho festival outfit colorful",
    "formal navy suit men's",
    "pink sequin going out dress",
    "vintage denim jacket cropped",
]

for query in demo_queries:
    print(f"\n{'='*70}")
    print(f"  🔍 \"{query}\"")

    parsed = engine.query_parser.parse(query)
    print(f"  Intent: cat={parsed.category_filter}, col={parsed.color_filter}, "
          f"price=[{parsed.price_min},{parsed.price_max}], tags={parsed.style_tags}")
    print(f"  CLIP text: \"{parsed.vibe_text}\"")
    print()

    results = engine.search(query, top_n=5)
    for _, row in results.iterrows():
        score = row.get('hybrid_score', 0)
        print(f"  [{score:.3f}] {row['name'][:52]}")
        print(f"          £{row['price']:.2f} | {row.get('color_clean', '')} "
              f"| {row.get('category', '')} | {row.get('brand', '')}")


# ── Visual grid display + Price proximity demo ──
# Compare: "under £10" now shows cheapest viable items instead of £200 products

print("=" * 70)
print("  PRICE PROXIMITY FIX DEMO")
print("=" * 70)

query = "floral dress under 30"
results = engine.search(query, top_n=10)
print(f"\n  Query: \"{query}\"")
print(f"  Results: {len(results)} items")
print(f"  Price range: £{results['price'].min():.2f} - £{results['price'].max():.2f}")
print(f"  (Cheapest leather jackets in catalog start at ~£16)\n")
display_results(results, max_display=10)

# ── Sorting demo ──
print("\n" + "=" * 70)
print("  SORTING DEMO")
print("=" * 70)

query2 = "floral dress summer"
results2 = engine.search(query2, top_n=10)
print(f"\n  Default (relevance sort):")
for _, r in results2.head(5).iterrows():
    print(f"    [{r.get('hybrid_score',0):.3f}] £{r['price']:6.2f}  {r['name'][:50]}")

# Re-sort by price ascending
sorted_asc = sort_results(results2, 'price_asc')
print(f"\n  Re-sorted by price (low to high):")
for _, r in sorted_asc.head(5).iterrows():
    print(f"    [{r.get('hybrid_score',0):.3f}] £{r['price']:6.2f}  {r['name'][:50]}")

# Sort directly from search
results3 = engine.search(query2, top_n=10, sort_by='price_desc')
print(f"\n  Searched with sort_by='price_desc' (high to low):")
for _, r in results3.head(5).iterrows():
    print(f"    [{r.get('hybrid_score',0):.3f}] £{r['price']:6.2f}  {r['name'][:50]}")



# ── Visual similarity: "More Like This" ──
sample_sku = str(engine.metadata['sku'].iloc[42])  # Pick any product
print(f"Finding products similar to: {engine.metadata.iloc[42]['name']}")
print(f"  SKU: {sample_sku} | £{engine.metadata.iloc[42]['price']:.2f} | {engine.metadata.iloc[42].get('category','')}")
print()

similar = engine.search_similar(sample_sku, top_n=5)
for _, row in similar.iterrows():
    print(f"  [sim={row['similarity_score']:.3f}] {row['name'][:50]}")
    print(f"          £{row['price']:.2f} | {row.get('color_clean', '')} | {row.get('category', '')}")

# ── Product detail page ──
print()
display_product_detail(engine, sample_sku)

# ── Complete the Look (v3.3: style-coherent outfits) ──
print()
print("=" * 60)
print("  COMPLETE THE LOOK (v3.3 — style-coherent)")
print("=" * 60)

# Find a dress to build an outfit around
dresses = engine.metadata[engine.metadata['category'] == 'Dresses']
if len(dresses) > 0:
    dress_row = dresses.iloc[5]  # Pick a specific dress
    dress_sku = str(dress_row['sku'])
    print(f"Building outfit around: {dress_row['name']}")
    print(f"  Color: {dress_row.get('color_family', 'N/A')} | Price: £{dress_row['price']:.2f}")
    print(f"  Style tags: {dress_row.get('style_tags', [])}")
    print()

    outfit = engine.complete_the_look(dress_sku, n_per_category=3)
    for cat, items_df in outfit.items():
        print(f"  {cat}:")
        for _, item in items_df.iterrows():
            print(f"    [score={item['outfit_score']:.3f}] {item['name'][:50]}")
            print(f"          £{item['price']:.2f} | {item.get('color_family', '')} | {item.get('brand', '')}")
        print()

    display_outfit(engine, dress_sku)
else:
    print("No dresses found in catalog.")


# ── Image-based search (upload your own!) ──
# To use: upload an image, then:
#
from PIL import Image
img = Image.open("sample_2.png")
results = engine.search_by_image(img, top_n=10)
# display_results(results)
#
# Or multimodal: "like this but in blue"
results = engine.search("like this but in black under 30", query_image=img, top_n=10)
display_results(results)

print("Image search ready — upload a fashion photo and use engine.search_by_image(img)")


# ── Build improved synthetic test queries from the dataset ──
# Strategy: for each test query, find products that genuinely match the criteria,
# use MORE relevant SKUs per query, and test with queries that include
# both exact-match terms and semantic intent.

import random

def build_synthetic_test(engine, n_queries=15, n_relevant=10):
    """
    Build synthetic ground truth by sampling products that match criteria.
    Uses more relevant SKUs and color_family values that MATCH the actual data.
    """
    test_set = []
    meta = engine.metadata

    # ── These filters now use LOWERCASE color_family values matching the data ──
    test_configs = [
        ("black dress under £40",
         {"category": "Dresses", "color_family": "black", "price_max": 40}),
        ("blue jeans",
         {"category": "Jeans", "color_family": "blue"}),
        ("red dress",
         {"category": "Dresses", "color_family": "red"}),
        ("green jacket",
         {"category": "Coats & Jackets", "color_family": "green"}),
        ("pink top under £20",
         {"category": "Tops", "color_family": "pink", "price_max": 20}),
        ("beige cardigan",
         {"category": "Knitwear", "color_family": "beige"}),
        ("purple dress",
         {"category": "Dresses", "color_family": "purple"}),
        ("black boots",
         {"category": "Shoes", "color_family": "black"}),
        ("white shirt",
         {"category": "Tops", "color_family": "white"}),
        ("navy blazer",
         {"category": "Coats & Jackets", "color_family": "navy"}),
        ("brown leather jacket",
         {"category": "Coats & Jackets", "color_family": "brown"}),
        ("grey hoodie",
         {"category": "Hoodies & Sweatshirts", "color_family": "grey"}),
        ("multi floral dress",
         {"category": "Dresses", "color_family": "multi"}),
        ("black trousers",
         {"category": "Trousers", "color_family": "black"}),
        ("blue denim jacket",
         {"category": "Coats & Jackets", "color_family": "blue"}),
    ]

    for query, filters in test_configs[:n_queries]:
        subset = meta.copy()
        for col, val in filters.items():
            if col == "price_max":
                subset = subset[subset["price"] <= val]
            elif col in subset.columns:
                subset = subset[subset[col].str.lower() == val.lower()]

        if len(subset) >= n_relevant:
            relevant_skus = subset.sample(n=n_relevant, random_state=42)["sku"].tolist()
            test_set.append({"query": query, "relevant_skus": relevant_skus})
        elif len(subset) >= 3:
            # Use whatever we have
            relevant_skus = subset.sample(n=min(len(subset), n_relevant), random_state=42)["sku"].tolist()
            test_set.append({"query": query, "relevant_skus": relevant_skus})

    return test_set

test_queries = build_synthetic_test(engine)
print(f"Built {len(test_queries)} synthetic test queries")
for tq in test_queries:
    print(f"  \"{tq['query']}\" -> {len(tq['relevant_skus'])} relevant SKUs")

# ── Run evaluation ──
evaluator = SearchEvaluator(engine)
report = evaluator.evaluate(test_queries, k_values=[5, 10, 20])
evaluator.print_report(report)

# ── Multilingual search demos ──
multilingual_queries = [
    # French
    "robe noir élégant",           # "elegant black dress"
    "veste cuir homme",            # "leather jacket men"
    "chaussures blanc femme",      # "white shoes women"
    # Spanish
    "vestido rojo barato",         # "cheap red dress"
    "chaqueta cuero negro",        # "black leather jacket"
    # German
    "schwarz kleid elegant",       # "elegant black dress"
    "blau hose herren",            # "blue trousers men"
    # Italian
    "abito nero donna",            # "black dress women"
]

print("=" * 70)
print("  MULTILINGUAL SEARCH DEMOS")
print("=" * 70)

for query in multilingual_queries:
    # Show translation
    translated, lang, was_translated = MultilingualHandler.translate_query(query)
    print(f"\n  [{lang}] \"{query}\"")
    if was_translated:
        print(f"    -> EN: \"{translated}\"")

    results = engine.search(query, top_n=3)
    for _, row in results.iterrows():
        score = row.get('hybrid_score', 0)
        print(f"    [{score:.3f}] {row['name'][:52]}")
        print(f"            £{row['price']:.2f} | {row.get('color_clean', '')} | {row.get('category', '')}")


# ── Spell correction demos ──
typo_queries = [
    "blak lether jaket",          # "black leather jacket"
    "floral mdi dress",            # "floral midi dress"
    "oversied hodie men",          # "oversized hoodie men"
    "whte sneekers casual",        # "white sneakers casual"
    "pnk sequin dres party",       # "pink sequin dress party"
    "dnim jackt cropped",          # "denim jacket cropped"
]

print("=" * 70)
print("  SPELL CORRECTION DEMOS")
print("=" * 70)

for query in typo_queries:
    corrected, was_corrected = engine.spell_corrector.correct_query(query)
    print(f"\n  Input:     \"{query}\"")
    if was_corrected:
        print(f"  Corrected: \"{corrected}\"")
    else:
        print(f"  (no correction needed)")

    results = engine.search(query, top_n=3)
    for _, row in results.iterrows():
        score = row.get('hybrid_score', 0)
        print(f"    [{score:.3f}] {row['name'][:52]}")
        print(f"            £{row['price']:.2f} | {row.get('color_clean', '')} | {row.get('category', '')}")

# Show the visual display with the "did you mean" banner
print(f"\n{'='*70}")
print("  VISUAL DISPLAY WITH SPELL CORRECTION BANNER")
print(f"{'='*70}")
results = engine.search("blak lether jaket edgy", top_n=5)
display_results(results)

# ── Size-aware filtering demos (v3.3) ──
print("=" * 60)
print("  SIZE-AWARE FILTERING")
print("=" * 60)

size_queries = [
    "size 10 black dress",
    "medium hoodie streetwear",
    "XL casual shirt for men",
    "size S midi skirt",
]

for q in size_queries:
    results = engine.search(q, top_n=5)
    qi = results.attrs.get('query_info', {})
    print(f"\nQuery: \"{q}\"")
    print(f"  Parsed size: {qi.get('parsed_size', 'None')}")
    print(f"  Parsed category: {qi.get('parsed_category', 'None')}")
    print(f"  Results: {len(results)}")
    for _, row in results.head(3).iterrows():
        sizes = row.get('sizes_available', [])
        size_str = ', '.join(sizes[:5]) if isinstance(sizes, list) else str(sizes)
        print(f"    {row['name'][:50]}  |  £{row['price']:.2f}  |  sizes: {size_str}")

# ── Material/fabric filtering demos (v3.3) ──
print("=" * 60)
print("  MATERIAL/FABRIC FILTERING")
print("=" * 60)

material_queries = [
    "silk midi dress",
    "leather jacket black",
    "cotton casual shirt",
    "velvet party dress",
    "denim jacket women",
]

for q in material_queries:
    results = engine.search(q, top_n=5)
    qi = results.attrs.get('query_info', {})
    print(f"\nQuery: \"{q}\"")
    print(f"  Parsed material: {qi.get('parsed_material', 'None')}")
    print(f"  Results: {len(results)}")
    for _, row in results.head(3).iterrows():
        mats = row.get('materials', [])
        mat_str = ', '.join(mats[:3]) if isinstance(mats, list) else str(mats)
        print(f"    {row['name'][:50]}  |  £{row['price']:.2f}  |  materials: {mat_str}")

# Visual display for one
print("\n--- Visual results for 'silk midi dress': ---")
results = engine.search("silk midi dress", top_n=10)
display_results(results)

# ── Negative/exclusion query demos (v3.3) ──
print("=" * 60)
print("  NEGATIVE/EXCLUSION QUERIES")
print("=" * 60)

exclusion_queries = [
    "black dress not floral",
    "casual jacket without leather",
    "summer top no black",
    "trainers excluding white",
]

for q in exclusion_queries:
    results = engine.search(q, top_n=5)
    qi = results.attrs.get('query_info', {})
    print(f"\nQuery: \"{q}\"")
    print(f"  Exclusions: {qi.get('parsed_exclusions', [])}")
    print(f"  Results: {len(results)}")
    for _, row in results.head(3).iterrows():
        print(f"    {row['name'][:50]}  |  £{row['price']:.2f}  |  {row.get('color_clean', '')}  |  {row.get('category', '')}")

# Visual display for one
print("\n--- Visual results for 'casual jacket without leather': ---")
results = engine.search("black jacket without leather", top_n=10)
display_results(results)



