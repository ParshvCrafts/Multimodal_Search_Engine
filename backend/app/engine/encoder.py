"""
engine/encoder.py

FashionCLIPEncoder — wraps a HuggingFace CLIP model for text and image encoding.
Extracted from finalized_search_engine_full_script.py (lines 482-652).
"""

import logging
from pathlib import Path
from typing import List, Optional

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

from backend.app.config import SearchConfig

logger = logging.getLogger(__name__)

__all__ = ["FashionCLIPEncoder"]


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
