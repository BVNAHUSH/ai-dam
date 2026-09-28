from pathlib import Path

from sqlalchemy.orm import Session

from app.config import FAISS_INDEX_PATH
from app.database.database import SessionLocal, init_database
from app.database.models import Asset

from app.search.embeddings import CLIPEmbedder
from app.search.faiss_index import FAISSIndex


def build_image_index(db: Session):

    project_root = (
        Path(__file__).resolve().parents[3]
    )

    index_path = (
        project_root
        / "data"
        / "images.index.faiss"
    )

    # ---------------------------------------------------------
    # Load completed image assets
    # ---------------------------------------------------------

    assets = (
        db.query(Asset)
        .filter(
            Asset.file_type == "image",
            Asset.status == "completed",
        )
        .order_by(Asset.id)
        .all()
    )

    print(
        f"Found {len(assets)} completed "
        f"image assets in SQLite."
    )

    if not assets:
        print(
            "No completed image assets found."
        )
        return

    # ---------------------------------------------------------
    # Load OpenCLIP
    # ---------------------------------------------------------

    embedder = CLIPEmbedder()

    # ---------------------------------------------------------
    # Create fresh FAISS index
    # ---------------------------------------------------------

    index = FAISSIndex(
        dimension=512,
        index_path=index_path,
    )

    # ---------------------------------------------------------
    # Add assets
    # ---------------------------------------------------------

    indexed = 0

    for position, asset in enumerate(
        assets,
        start=1,
    ):

        file_path = Path(
            asset.file_path
        )

        print(
            f"[{position}/{len(assets)}] "
            f"Asset {asset.id}: "
            f"{asset.filename}"
        )

        if not file_path.exists():

            print(
                "    ! File missing - skipped"
            )

            continue

        try:

            vector = embedder.embed_image(
                file_path
            )

            index.add(
                asset_id=asset.id,
                vector=vector,
            )

            indexed += 1

        except Exception as exc:

            print(
                f"    ! Embedding failed: "
                f"{exc}"
            )

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------

    index.save()

    print("\n==============================")
    print("FAISS INDEX COMPLETE")
    print("==============================")

    print(
        "SQLite assets:",
        len(assets),
    )

    print(
        "Indexed vectors:",
        indexed,
    )

    print(
        "FAISS size:",
        index.size,
    )

    print(
        "Index path:",
        index_path,
    )


if __name__ == "__main__":

    init_database()

    db = SessionLocal()

    try:

        build_image_index(db)

    finally:

        db.close()