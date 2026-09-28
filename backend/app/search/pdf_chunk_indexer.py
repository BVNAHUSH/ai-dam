from pathlib import Path

import fitz
import numpy as np

from app.config import DATASET_PATH
from app.database.database import SessionLocal
from app.database.models import Asset, PDFChunk
from app.search.pdf_embeddings import PDFEmbedder
from app.search.pdf_faiss_index import PDFChunkFAISSIndex


CHUNK_SIZE = 80
CHUNK_OVERLAP = 20

DIMENSION = 384

PDF_INDEX_PATH = (
    DATASET_PATH.parent
    / "data"
    / "pdf_chunks.index.faiss"
)


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
):
    words = text.split()

    if not words:
        return []

    if overlap >= chunk_size:
        raise ValueError(
            "CHUNK_OVERLAP must be smaller than CHUNK_SIZE."
        )

    chunks = []

    step = chunk_size - overlap

    for start in range(
        0,
        len(words),
        step,
    ):
        chunk_words = words[
            start:start + chunk_size
        ]

        if not chunk_words:
            break

        chunks.append(
            " ".join(chunk_words)
        )

        if (
            start + chunk_size
            >= len(words)
        ):
            break

    return chunks


def extract_pdf_chunks(pdf_path: Path):
    """
    Extract text page-by-page and create
    overlapping chunks within each page.
    """

    results = []

    document = fitz.open(
        str(pdf_path)
    )

    try:
        for page_index in range(
            len(document)
        ):
            page = document[
                page_index
            ]

            text = page.get_text(
                "text"
            ).strip()

            if not text:
                continue

            chunks = chunk_text(text)

            for chunk_index, chunk in enumerate(
                chunks
            ):
                if not chunk.strip():
                    continue

                results.append(
                    {
                        "page_number": page_index + 1,
                        "chunk_index": chunk_index,
                        "text": chunk,
                    }
                )

    finally:
        document.close()

    return results


def vector_to_bytes(vector):
    vector = np.asarray(
        vector,
        dtype=np.float32,
    )

    return vector.tobytes()


def build_pdf_chunk_index():

    print("=" * 70)
    print("PDF CHUNK INDEXER - MiniLM")
    print("=" * 70)

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Load document embedding model
        # ----------------------------------------------------

        print()
        print(
            "Loading PDF text embedding model..."
        )

        embedder = PDFEmbedder()

        print()
        print(
            "PDF embedding model ready."
        )

        # ----------------------------------------------------
        # Find PDFs
        # ----------------------------------------------------

        assets = (
            db.query(Asset)
            .filter(
                Asset.file_type == "pdf",
                Asset.status != "duplicate",
            )
            .order_by(Asset.id)
            .all()
        )

        print()
        print(
            f"PDF assets found: {len(assets)}"
        )

        if not assets:
            print(
                "No PDF assets found."
            )
            return

        # ----------------------------------------------------
        # Delete old PDF chunks
        # ----------------------------------------------------

        print()
        print(
            "Removing old PDF chunks..."
        )

        db.query(PDFChunk).delete()

        db.commit()

        # ----------------------------------------------------
        # Create NEW 384-dimensional FAISS
        # ----------------------------------------------------

        faiss_index = PDFChunkFAISSIndex(
            dimension=DIMENSION,
            index_path=PDF_INDEX_PATH,
        )

        total_chunks = 0
        successful_chunks = 0
        failed_chunks = 0

        # ----------------------------------------------------
        # Process PDFs
        # ----------------------------------------------------

        for pdf_number, asset in enumerate(
            assets,
            start=1,
        ):

            pdf_path = Path(
                asset.file_path
            )

            print()
            print(
                f"[{pdf_number}/{len(assets)}] "
                f"{asset.filename}"
            )

            if not pdf_path.exists():

                print(
                    "  ERROR: file not found"
                )

                failed_chunks += 1
                continue

            # -----------------------------------------------
            # Extract chunks
            # -----------------------------------------------

            try:

                chunks = extract_pdf_chunks(
                    pdf_path
                )

            except Exception as exc:

                print(
                    f"  ERROR extracting PDF: {exc}"
                )

                failed_chunks += 1
                continue

            print(
                f"  Text chunks: {len(chunks)}"
            )

            if not chunks:
                print(
                    "  WARNING: no extractable text"
                )
                continue

            total_chunks += len(chunks)

            # -----------------------------------------------
            # Embed chunks
            # -----------------------------------------------

            for chunk_number, chunk_data in enumerate(
                chunks,
                start=1,
            ):

                try:

                    vector = embedder.embed_text(
                        chunk_data["text"]
                    )

                    vector = np.asarray(
                        vector,
                        dtype=np.float32,
                    )

                    if vector.shape[0] != DIMENSION:

                        raise ValueError(
                            "Unexpected embedding "
                            f"dimension: "
                            f"{vector.shape[0]}"
                        )

                    # ---------------------------------------
                    # Store chunk
                    # ---------------------------------------

                    chunk_record = PDFChunk(
                        asset_id=asset.id,
                        page_number=chunk_data[
                            "page_number"
                        ],
                        chunk_index=chunk_data[
                            "chunk_index"
                        ],
                        text=chunk_data[
                            "text"
                        ],
                        embedding=vector_to_bytes(
                            vector
                        ),
                        embedding_status="completed",
                        embedding_model=(
                            PDFEmbedder.MODEL_NAME
                        ),
                        embedding_dimension=DIMENSION,
                    )

                    db.add(
                        chunk_record
                    )

                    db.flush()

                    # ---------------------------------------
                    # Add to FAISS
                    # ---------------------------------------

                    faiss_index.add(
                        chunk_record.id,
                        vector,
                    )

                    successful_chunks += 1

                    print(
                        f"\r  Embedding chunks: "
                        f"{chunk_number}/"
                        f"{len(chunks)}",
                        end="",
                        flush=True,
                    )

                except Exception as exc:

                    failed_chunks += 1

                    print()

                    print(
                        f"  ERROR in chunk "
                        f"{chunk_number}: {exc}"
                    )

            print()

            # Commit after each PDF
            db.commit()

        # ----------------------------------------------------
        # Save FAISS
        # ----------------------------------------------------

        print()
        print(
            "Saving PDF FAISS index..."
        )

        faiss_index.save()

        print()
        print("=" * 70)
        print("PDF INDEXING COMPLETE")
        print("=" * 70)

        print(
            f"PDF assets:       {len(assets)}"
        )

        print(
            f"Total chunks:     {total_chunks}"
        )

        print(
            f"Successful:       {successful_chunks}"
        )

        print(
            f"Failed:           {failed_chunks}"
        )

        print(
            f"FAISS vectors:    {faiss_index.size}"
        )

        print(
            f"Embedding model:  {PDFEmbedder.MODEL_NAME}"
        )

        print(
            f"Embedding dim:    {DIMENSION}"
        )

        print(
            f"Index file:       {PDF_INDEX_PATH}"
        )

        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    build_pdf_chunk_index()