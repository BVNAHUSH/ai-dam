from pathlib import Path

import faiss
import numpy as np


class PDFChunkFAISSIndex:
    """
    FAISS index specifically for PDF text chunks.

    Each vector maps to a PDFChunk database ID.
    """

    def __init__(
        self,
        dimension: int = 384,
        index_path: Path | None = None,
    ):
        self.dimension = dimension

        self.index_path = (
            index_path
            or Path("data/pdf_chunks.index.faiss")
        )

        self.index = faiss.IndexFlatIP(
            self.dimension
        )

        self.chunk_ids: list[int] = []

    # =========================================================
    # ADD
    # =========================================================

    def add(
        self,
        chunk_id: int,
        vector,
    ):
        vector = np.asarray(
            vector,
            dtype=np.float32,
        ).reshape(1, -1)

        if vector.shape[1] != self.dimension:
            raise ValueError(
                f"Expected embedding dimension "
                f"{self.dimension}, "
                f"got {vector.shape[1]}"
            )

        faiss.normalize_L2(vector)

        self.index.add(vector)

        self.chunk_ids.append(
            int(chunk_id)
        )

    # =========================================================
    # SEARCH
    # =========================================================

    def search(
        self,
        vector,
        top_k: int = 20,
    ):
        if self.index.ntotal == 0:
            return []

        vector = np.asarray(
            vector,
            dtype=np.float32,
        ).reshape(1, -1)

        if vector.shape[1] != self.dimension:
            raise ValueError(
                f"Expected embedding dimension "
                f"{self.dimension}, "
                f"got {vector.shape[1]}"
            )

        faiss.normalize_L2(vector)

        k = min(
            top_k,
            self.index.ntotal,
        )

        scores, indices = (
            self.index.search(
                vector,
                k,
            )
        )

        results = []

        for score, index_position in zip(
            scores[0],
            indices[0],
        ):
            if index_position < 0:
                continue

            chunk_id = self.chunk_ids[
                int(index_position)
            ]

            results.append(
                {
                    "chunk_id": int(
                        chunk_id
                    ),
                    "score": float(
                        score
                    ),
                }
            )

        return results

    # =========================================================
    # SAVE
    # =========================================================

    def save(self):
        self.index_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        faiss.write_index(
            self.index,
            str(self.index_path),
        )

        ids_path = (
            self.index_path.with_suffix(
                ".ids.npy"
            )
        )

        np.save(
            ids_path,
            np.asarray(
                self.chunk_ids,
                dtype=np.int64,
            ),
        )

    # =========================================================
    # LOAD
    # =========================================================

    def load(self):
        if not self.index_path.exists():
            return False

        ids_path = (
            self.index_path.with_suffix(
                ".ids.npy"
            )
        )

        if not ids_path.exists():
            return False

        self.index = faiss.read_index(
            str(self.index_path)
        )

        self.chunk_ids = (
            np.load(ids_path)
            .astype(np.int64)
            .tolist()
        )

        if (
            len(self.chunk_ids)
            != self.index.ntotal
        ):
            raise RuntimeError(
                "PDF FAISS index and "
                "chunk ID mapping have "
                "different sizes."
            )

        return True

    @property
    def size(self):
        return self.index.ntotal