import os
import sys
import logging
from pathlib import Path
from dataclasses import dataclass
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
