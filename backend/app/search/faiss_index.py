from pathlib import Path

import faiss
import numpy as np


class FAISSIndex:

    def __init__(
        self,
        dimension: int = 512,
        index_path: Path | None = None,
    ):
        self.dimension = dimension

        self.index_path = (
            index_path
            or Path("data/index.faiss")
        )

        self.index = faiss.IndexFlatIP(
            self.dimension
        )

        self.asset_ids: list[int] = []

    def add(
        self,
        asset_id: int,
        vector: np.ndarray,
    ):
        vector = np.asarray(
            vector,
            dtype=np.float32,
        ).reshape(1, -1)

        faiss.normalize_L2(vector)

        self.index.add(vector)

        self.asset_ids.append(
            int(asset_id)
        )

    def search(
        self,
        vector: np.ndarray,
        top_k: int = 10,
    ):
        if self.index.ntotal == 0:
            return []

        vector = np.asarray(
            vector,
            dtype=np.float32,
        ).reshape(1, -1)

        faiss.normalize_L2(vector)

        scores, indices = self.index.search(
            vector,
            min(top_k, self.index.ntotal),
        )

        results = []

        for score, index_position in zip(
            scores[0],
            indices[0],
        ):
            if index_position < 0:
                continue

            asset_id = self.asset_ids[
                int(index_position)
            ]

            results.append(
                {
                    "asset_id": asset_id,
                    "score": float(score),
                }
            )

        return results

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
                self.asset_ids,
                dtype=np.int64,
            ),
        )

    def load(self):

        if not self.index_path.exists():
            return False

        self.index = faiss.read_index(
            str(self.index_path)
        )

        ids_path = (
            self.index_path.with_suffix(
                ".ids.npy"
            )
        )

        if not ids_path.exists():
            return False

        self.asset_ids = (
            np.load(
                ids_path
            )
            .astype(np.int64)
            .tolist()
        )

        return True

    @property
    def size(self):
        return self.index.ntotal