from threading import Thread

from fastapi import APIRouter, HTTPException

from app.config import FAISS_INDEX_PATH
from app.database.database import SessionLocal
from app.ingestion.indexing_status import indexing_status
from app.search.multimodal_indexer import MultimodalIndexer


router = APIRouter(
    prefix="/api/indexing",
    tags=["Indexing"],
)


def run_local_indexing():
    db = SessionLocal()

    try:
        # Count assets for progress reporting
        from app.database.models import Asset

        assets = (
            db.query(Asset)
            .filter(Asset.status != "duplicate")
            .all()
        )

        indexing_status.start(len(assets))

        indexer = MultimodalIndexer(
            db=db,
            index_path=FAISS_INDEX_PATH,
        )

        # Run the existing LOCAL OpenCLIP pipeline
        indexer.index_assets()

        # Mark everything as processed for the UI
        for asset in assets:
            indexing_status.update_current(
                asset.filename,
                asset.file_type,
            )

            if asset.embedding_status == "completed":
                indexing_status.record_result("completed")
            elif asset.embedding_status == "failed":
                indexing_status.record_result("failed")
            else:
                indexing_status.record_result("skipped")

    except Exception as exc:
        print(f"LOCAL INDEXING ERROR: {exc}")

    finally:
        indexing_status.finish()
        db.close()


@router.get("/status")
def get_indexing_status():
    return indexing_status.get()


@router.post("/start")
def start_indexing():

    status = indexing_status.get()

    if status["running"]:
        raise HTTPException(
            status_code=409,
            detail="Indexing is already running.",
        )

    thread = Thread(
        target=run_local_indexing,
        daemon=True,
    )

    thread.start()

    return {
        "message": "Local indexing started."
    }