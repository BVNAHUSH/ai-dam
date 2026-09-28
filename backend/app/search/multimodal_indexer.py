from pathlib import Path

import cv2
import numpy as np
from sqlalchemy.orm import Session

from app.database.models import Asset
from app.search.embeddings import CLIPEmbedder
from app.search.faiss_index import FAISSIndex


class MultimodalIndexer:

    MODEL_NAME = "openai/ViT-B-32"
    DIMENSION = 512

    def __init__(
        self,
        db: Session,
        index_path: Path,
    ):
        self.db = db

        self.embedder = CLIPEmbedder()

        self.index = FAISSIndex(
            dimension=self.DIMENSION,
            index_path=index_path,
        )

    # =========================================================
    # IMAGE
    # =========================================================

    def embed_image(
        self,
        file_path: Path,
    ) -> np.ndarray:

        return self.embedder.embed_image(
            file_path
        )

    # =========================================================
    # VIDEO FRAME EXTRACTION
    # =========================================================

    def extract_video_frames(
        self,
        file_path: Path,
        number_of_frames: int = 8,
    ):

        capture = cv2.VideoCapture(
            str(file_path)
        )

        if not capture.isOpened():
            raise RuntimeError(
                f"Could not open video: {file_path}"
            )

        total_frames = int(
            capture.get(
                cv2.CAP_PROP_FRAME_COUNT
            )
        )

        if total_frames <= 0:
            capture.release()

            raise RuntimeError(
                "Video has no readable frames."
            )

        number_of_frames = min(
            number_of_frames,
            total_frames,
        )

        positions = [
            int(
                i
                * (total_frames - 1)
                / max(number_of_frames - 1, 1)
            )
            for i in range(number_of_frames)
        ]

        frames = []

        for position in positions:

            capture.set(
                cv2.CAP_PROP_POS_FRAMES,
                position,
            )

            success, frame = capture.read()

            if not success:
                continue

            success, encoded = cv2.imencode(
                ".jpg",
                frame,
                [
                    cv2.IMWRITE_JPEG_QUALITY,
                    80,
                ],
            )

            if success:
                frames.append(
                    encoded.tobytes()
                )

        capture.release()

        return frames

    # =========================================================
    # VIDEO
    # =========================================================

    def embed_video(
        self,
        file_path: Path,
    ) -> np.ndarray:

        frames = self.extract_video_frames(
            file_path,
            number_of_frames=8,
        )

        if not frames:
            raise RuntimeError(
                "No representative frames extracted."
            )

        vectors = []

        for frame_bytes in frames:

            vector = (
                self.embedder.embed_image_bytes(
                    frame_bytes
                )
            )

            vectors.append(vector)

        vectors = np.asarray(
            vectors,
            dtype=np.float32,
        )

        video_vector = vectors.mean(
            axis=0
        )

        norm = np.linalg.norm(
            video_vector
        )

        if norm > 0:
            video_vector /= norm

        return video_vector.astype(
            np.float32
        )

    # =========================================================
    # PDF
    # =========================================================

    def embed_pdf(
        self,
        text: str,
    ) -> np.ndarray:

        if not text or not text.strip():
            raise RuntimeError(
                "PDF contains no extractable text."
            )

        words = text.split()

        chunk_size = 60

        chunks = []

        for start in range(
            0,
            len(words),
            chunk_size,
        ):

            chunk = " ".join(
                words[
                    start:start + chunk_size
                ]
            )

            if chunk.strip():
                chunks.append(chunk)

        # Avoid extremely large PDFs
        chunks = chunks[:30]

        vectors = []

        for chunk in chunks:

            vector = (
                self.embedder.embed_text(
                    chunk
                )
            )

            vectors.append(vector)

        vectors = np.asarray(
            vectors,
            dtype=np.float32,
        )

        pdf_vector = vectors.mean(
            axis=0
        )

        norm = np.linalg.norm(
            pdf_vector
        )

        if norm > 0:
            pdf_vector /= norm

        return pdf_vector.astype(
            np.float32
        )

    # =========================================================
    # EMBEDDING GENERATION
    # =========================================================

    def generate_embedding(
        self,
        asset: Asset,
    ) -> np.ndarray:

        file_path = Path(
            asset.file_path
        )

        if not file_path.exists():
            raise RuntimeError(
                f"File does not exist: {file_path}"
            )

        if asset.file_type == "image":

            return self.embed_image(
                file_path
            )

        if asset.file_type == "video":

            return self.embed_video(
                file_path
            )

        if asset.file_type == "pdf":

            return self.embed_pdf(
                asset.extracted_text or ""
            )

        raise RuntimeError(
            f"Unsupported asset type: "
            f"{asset.file_type}"
        )

    # =========================================================
    # STORE EMBEDDING IN SQLITE
    # =========================================================

    def store_embedding(
        self,
        asset: Asset,
        vector: np.ndarray,
    ):

        vector = np.asarray(
            vector,
            dtype=np.float32,
        )

        # Normalize before storage
        norm = np.linalg.norm(vector)

        if norm > 0:
            vector = vector / norm

        asset.embedding = vector.tobytes()

        asset.embedding_status = (
            "completed"
        )

        asset.embedding_model = (
            self.MODEL_NAME
        )

        asset.embedding_dimension = (
            self.DIMENSION
        )

    # =========================================================
    # LOAD EMBEDDING FROM SQLITE
    # =========================================================

    def load_embedding(
        self,
        asset: Asset,
    ):

        if not asset.embedding:
            return None

        if (
            asset.embedding_dimension
            != self.DIMENSION
        ):
            return None

        vector = np.frombuffer(
            asset.embedding,
            dtype=np.float32,
        ).copy()

        if vector.shape[0] != self.DIMENSION:
            return None

        return vector

    # =========================================================
    # BUILD FAISS INDEX
    # =========================================================

    def rebuild_faiss_index(self):

        print()
        print("=" * 45)
        print("BUILDING FAISS INDEX")
        print("=" * 45)

        # Start with a completely fresh FAISS index.
        #
        # This is intentional:
        # SQLite is our persistent source of truth.
        #
        # FAISS is the searchable derived index.

        self.index = FAISSIndex(
            dimension=self.DIMENSION,
            index_path=self.index.index_path,
        )

        assets = (
            self.db.query(Asset)
            .filter(
                Asset.status != "duplicate",
                 Asset.file_type.in_(["image", "video"]),
            )
            .filter(
                Asset.embedding_status
                == "completed"
            )
            .order_by(Asset.id)
            .all()
        )

        added = 0

        for asset in assets:

            vector = self.load_embedding(
                asset
            )

            if vector is None:
                continue

            self.index.add(
                asset_id=asset.id,
                vector=vector,
            )

            added += 1

        self.index.save()

        print(
            f"FAISS vectors : {added}"
        )

        return added

    # =========================================================
    # MAIN INDEXING PIPELINE
    # =========================================================

    def index_assets(self):

        assets = (
            self.db.query(Asset)
            .filter(
                Asset.status != "duplicate"
            )
            .order_by(Asset.id)
            .all()
        )

        print(
            f"Assets discovered: {len(assets)}"
        )

        stats = {
            "completed": 0,
            "skipped": 0,
            "failed": 0,
        }

        # -----------------------------------------------------
        # Generate missing embeddings
        # -----------------------------------------------------

        for position, asset in enumerate(
            assets,
            start=1,
        ):

            print(
                f"\n[{position}/{len(assets)}] "
                f"{asset.file_type.upper():5} "
                f"{asset.filename}"
            )

            # -------------------------------------------------
            # Persistent embedding already exists
            # -------------------------------------------------

            if (
                asset.embedding_status
                == "completed"
                and asset.embedding
            ):

                stats["skipped"] += 1

                print(
                    "    → embedding already stored"
                )

                continue

            try:

                vector = self.generate_embedding(
                    asset
                )

                self.store_embedding(
                    asset,
                    vector,
                )

                stats["completed"] += 1

                print(
                    "    ✓ embedding generated"
                )

            except Exception as exc:

                asset.embedding_status = (
                    "failed"
                )

                asset.error_message = str(
                    exc
                )

                stats["failed"] += 1

                print(
                    f"    ✗ failed: {exc}"
                )

        # -----------------------------------------------------
        # Persist embeddings
        # -----------------------------------------------------

        self.db.commit()

        # -----------------------------------------------------
        # Rebuild FAISS from ALL stored embeddings
        # -----------------------------------------------------

        faiss_size = (
            self.rebuild_faiss_index()
        )

        # -----------------------------------------------------
        # Final report
        # -----------------------------------------------------

        print()
        print("=" * 45)
        print("MULTIMODAL INDEX COMPLETE")
        print("=" * 45)

        print(
            f"New embeddings : "
            f"{stats['completed']}"
        )

        print(
            f"Skipped        : "
            f"{stats['skipped']}"
        )

        print(
            f"Failed         : "
            f"{stats['failed']}"
        )

        print(
            f"FAISS vectors  : "
            f"{faiss_size}"
        )

        return stats