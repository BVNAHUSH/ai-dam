from pathlib import Path
import os

from sqlalchemy.orm import Session

from app.config import FAISS_INDEX_PATH, DATASET_PATH
from app.database.models import Asset, PDFChunk
from app.search.embeddings import CLIPEmbedder
from app.search.pdf_embeddings import PDFEmbedder
from app.search.faiss_index import FAISSIndex
from app.search.pdf_faiss_index import PDFChunkFAISSIndex


class SearchService:
    """
    Multimodal semantic search.

    Images / Videos:
        Query
          ↓
        OpenCLIP
          ↓
        Main FAISS
          ↓
        Asset

    PDFs:
        Query
          ↓
        MiniLM text embedding
          ↓
        PDF chunk FAISS
          ↓
        Matching chunk
          ↓
        PDF + page + snippet
    """

    IMAGE_VIDEO_THRESHOLD = float(
        os.getenv(
            "SEARCH_IMAGE_VIDEO_THRESHOLD",
            "0.27",
        )
    )

    PDF_THRESHOLD = float(
        os.getenv(
            "SEARCH_PDF_THRESHOLD",
            "0.30",
        )
    )

    def __init__(
        self,
        db: Session,
        index_path: Path | None = None,
    ):
        self.db = db

        # =====================================================
        # IMAGE / VIDEO EMBEDDER
        # =====================================================

        self.embedder = CLIPEmbedder()

        # =====================================================
        # PDF TEXT EMBEDDER
        # =====================================================

        self.pdf_embedder = PDFEmbedder()

        # =====================================================
        # IMAGE / VIDEO FAISS
        # =====================================================

        self.index_path = (
            index_path
            or FAISS_INDEX_PATH
        )

        self.index = FAISSIndex(
            dimension=512,
            index_path=self.index_path,
        )

        if not self.index.load():
            raise RuntimeError(
                "Main FAISS index could not be loaded. "
                "Run the multimodal indexer first."
            )

        # =====================================================
        # PDF FAISS
        # =====================================================

        pdf_index_path = (
            DATASET_PATH.parent
            / "data"
            / "pdf_chunks.index.faiss"
        )

        self.pdf_index = PDFChunkFAISSIndex(
            dimension=384,
            index_path=pdf_index_path,
        )

        if not self.pdf_index.load():
            raise RuntimeError(
                "PDF chunk FAISS index could not be loaded. "
                "Run the PDF chunk indexer first."
            )

    # =========================================================
    # SEARCH
    # =========================================================

    def search(
        self,
        query: str,
        top_k: int = 20,
        file_type: str | None = None,
    ):
        query = query.strip()

        if not query:
            return []

        if file_type:
            file_type = file_type.lower()

            if file_type not in {
                "image",
                "video",
                "pdf",
            }:
                raise ValueError(
                    "file_type must be image, video, or pdf"
                )

        results = []

        # -----------------------------------------------------
        # Images / Videos
        # -----------------------------------------------------

        if file_type in (
            None,
            "image",
            "video",
        ):
            clip_query_vector = (
                self.embedder.embed_text(
                    query
                )
            )

            results.extend(
                self._search_assets(
                    query_vector=clip_query_vector,
                    top_k=top_k,
                    file_type=file_type,
                )
            )

        # -----------------------------------------------------
        # PDFs
        # -----------------------------------------------------

        if file_type in (
            None,
            "pdf",
        ):
            pdf_query_vector = (
                self.pdf_embedder.embed_text(
                    query
                )
            )

            results.extend(
                self._search_pdfs(
                    query_vector=pdf_query_vector,
                    top_k=top_k,
                )
            )

        # -----------------------------------------------------
        # Final ranking
        # -----------------------------------------------------

        results.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return results[:top_k]

    # =========================================================
    # IMAGE / VIDEO SEARCH
    # =========================================================

    def _search_assets(
        self,
        query_vector,
        top_k: int,
        file_type: str | None,
    ):
        candidate_k = min(
            max(top_k * 5, 50),
            self.index.size,
        )

        matches = self.index.search(
            query_vector,
            top_k=candidate_k,
        )

        if not matches:
            return []

        matches = [
            match
            for match in matches
            if match["score"]
            >= self.IMAGE_VIDEO_THRESHOLD
        ]

        if not matches:
            return []

        asset_ids = [
            match["asset_id"]
            for match in matches
        ]

        assets = (
            self.db.query(Asset)
            .filter(
                Asset.id.in_(asset_ids)
            )
            .all()
        )

        asset_map = {
            asset.id: asset
            for asset in assets
        }

        results = []

        for match in matches:

            asset = asset_map.get(
                match["asset_id"]
            )

            if asset is None:
                continue

            if asset.status == "duplicate":
                continue

            if asset.embedding_status != "completed":
                continue

            # PDFs are handled exclusively by
            # the dedicated PDF chunk index.
            if asset.file_type == "pdf":
                continue

            if (
                file_type
                and asset.file_type != file_type
            ):
                continue

            results.append(
                {
                    "id": asset.id,
                    "filename": asset.filename,
                    "file_path": asset.file_path,
                    "file_type": asset.file_type,
                    "mime_type": asset.mime_type,
                    "file_size": asset.file_size,
                    "width": asset.width,
                    "height": asset.height,
                    "duration": asset.duration,
                    "description": asset.description,
                    "extracted_text": (
                        asset.extracted_text[:500]
                        if asset.extracted_text
                        else None
                    ),
                    "score": round(
                        float(match["score"]),
                        4,
                    ),
                }
            )

            if len(results) >= top_k:
                break

        return results

    # =========================================================
    # PDF SEARCH
    # =========================================================

    def _search_pdfs(
        self,
        query_vector,
        top_k: int,
    ):
        if self.pdf_index.size == 0:
            return []

        chunk_candidate_k = min(
            max(top_k * 10, 50),
            self.pdf_index.size,
        )

        matches = self.pdf_index.search(
            query_vector,
            top_k=chunk_candidate_k,
        )

        if not matches:
            return []

        # -----------------------------------------------------
        # PDF-specific relevance threshold
        # -----------------------------------------------------

        matches = [
            match
            for match in matches
            if match["score"]
            >= self.PDF_THRESHOLD
        ]

        if not matches:
            return []

        chunk_ids = [
            match["chunk_id"]
            for match in matches
        ]

        chunks = (
            self.db.query(PDFChunk)
            .filter(
                PDFChunk.id.in_(chunk_ids)
            )
            .all()
        )

        chunk_map = {
            chunk.id: chunk
            for chunk in chunks
        }

        asset_ids = list(
            {
                chunk.asset_id
                for chunk in chunks
            }
        )

        assets = (
            self.db.query(Asset)
            .filter(
                Asset.id.in_(asset_ids)
            )
            .all()
        )

        asset_map = {
            asset.id: asset
            for asset in assets
        }

        # -----------------------------------------------------
        # Keep strongest matching chunk per PDF
        # -----------------------------------------------------

        best_by_asset = {}

        for match in matches:

            chunk = chunk_map.get(
                match["chunk_id"]
            )

            if chunk is None:
                continue

            asset = asset_map.get(
                chunk.asset_id
            )

            if asset is None:
                continue

            if asset.status == "duplicate":
                continue

            if asset.file_type != "pdf":
                continue

            score = float(
                match["score"]
            )

            existing = best_by_asset.get(
                asset.id
            )

            if (
                existing is None
                or score > existing["score"]
            ):
                best_by_asset[
                    asset.id
                ] = {
                    "asset": asset,
                    "chunk": chunk,
                    "score": score,
                }

        results = []

        for item in best_by_asset.values():

            asset = item["asset"]
            chunk = item["chunk"]

            results.append(
                {
                    "id": asset.id,
                    "filename": asset.filename,
                    "file_path": asset.file_path,
                    "file_type": "pdf",
                    "mime_type": asset.mime_type,
                    "file_size": asset.file_size,
                    "width": asset.width,
                    "height": asset.height,
                    "duration": asset.duration,
                    "description": asset.description,

                    "match_page": (
                        chunk.page_number
                    ),

                    "match_text": (
                        chunk.text[:500]
                    ),

                    "score": round(
                        item["score"],
                        4,
                    ),
                }
            )

        results.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return results[:top_k]