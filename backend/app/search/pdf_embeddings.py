from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


class PDFEmbedder:
    """
    Text embedding model specifically for PDF/document retrieval.

    Unlike the OpenCLIP embedder used for images/videos,
    this model is optimized for semantic text similarity.
    """

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    DIMENSION = 384

    def __init__(self):
        print("Loading PDF text embedding model...")

        self.device = "cuda" if self._cuda_available() else "cpu"

        print(f"PDF embedding device: {self.device}")

        self.model = SentenceTransformer(
            self.MODEL_NAME,
            device=self.device,
        )

        print("PDF text embedding model loaded.")

    @staticmethod
    def _cuda_available():
        try:
            import torch

            return torch.cuda.is_available()
        except Exception:
            return False

    def embed_text(self, text: str):
        if not text or not text.strip():
            raise ValueError(
                "Cannot embed empty PDF text."
            )

        vector = self.model.encode(
            text,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        return np.asarray(
            vector,
            dtype=np.float32,
        )