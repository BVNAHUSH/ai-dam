from pathlib import Path

from app.database.database import (
    SessionLocal,
    init_database,
)

from app.search.multimodal_indexer import (
    MultimodalIndexer,
)


if __name__ == "__main__":

    init_database()

    project_root = (
        Path(__file__).resolve().parents[3]
    )

    index_path = (
        project_root
        / "data"
        / "multimodal.index.faiss"
    )

    db = SessionLocal()

    try:

        indexer = MultimodalIndexer(
            db=db,
            index_path=index_path,
        )

        indexer.index_assets()

    finally:

        db.close()