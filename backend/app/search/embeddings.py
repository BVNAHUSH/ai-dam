from pathlib import Path
import io

import numpy as np
import torch
import open_clip
from PIL import Image


class CLIPEmbedder:
    """
    OpenCLIP-based multimodal embedding model.

    Supports:
    - Images
    - Image bytes / video frames
    - Text

    All embeddings are normalized 512-dimensional vectors,
    allowing cosine similarity through FAISS inner product.
    """

    def __init__(
        self,
        model_name: str = "ViT-B-32",
        pretrained: str = "openai",
    ):
        print("Loading OpenCLIP model...")

        self.device = (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        print(f"Device: {self.device}")

        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            model_name,
            pretrained=pretrained,
            device=self.device,
        )

        self.tokenizer = open_clip.get_tokenizer(model_name)

        self.model.eval()

        print("OpenCLIP model loaded.")

    # ---------------------------------------------------------
    # IMAGE FILE
    # ---------------------------------------------------------

    def embed_image(self, file_path: Path) -> np.ndarray:
        """
        Generate an embedding for an image file.
        """

        image = Image.open(file_path).convert("RGB")

        return self._embed_pil_image(image)

    # ---------------------------------------------------------
    # IMAGE BYTES
    # ---------------------------------------------------------

    def embed_image_bytes(
        self,
        image_bytes: bytes,
    ) -> np.ndarray:
        """
        Generate an embedding directly from image bytes.

        This is used for video representative frames.
        """

        image = Image.open(
            io.BytesIO(image_bytes)
        ).convert("RGB")

        return self._embed_pil_image(image)

    # ---------------------------------------------------------
    # INTERNAL IMAGE EMBEDDING
    # ---------------------------------------------------------

    def _embed_pil_image(
        self,
        image: Image.Image,
    ) -> np.ndarray:
        """
        Convert a PIL image into a normalized CLIP vector.
        """

        image_tensor = (
            self.preprocess(image)
            .unsqueeze(0)
            .to(self.device)
        )

        with torch.no_grad():

            features = self.model.encode_image(
                image_tensor
            )

            features /= features.norm(
                dim=-1,
                keepdim=True,
            )

        return (
            features
            .cpu()
            .numpy()
            .astype("float32")[0]
        )

    # ---------------------------------------------------------
    # TEXT
    # ---------------------------------------------------------

    def embed_text(
        self,
        text: str,
    ) -> np.ndarray:
        """
        Generate a normalized CLIP embedding for text.
        """

        if not text or not text.strip():
            raise ValueError(
                "Cannot embed empty text."
            )

        tokens = self.tokenizer(
            [text]
        ).to(self.device)

        with torch.no_grad():

            features = self.model.encode_text(
                tokens
            )

            features /= features.norm(
                dim=-1,
                keepdim=True,
            )

        return (
            features
            .cpu()
            .numpy()
            .astype("float32")[0]
        )