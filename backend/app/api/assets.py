from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import Asset


router = APIRouter(
    prefix="/api/assets",
    tags=["Assets"],
)


def asset_to_dict(asset: Asset):
    return {
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
            asset.extracted_text[:2000]
            if asset.extracted_text
            else None
        ),
        "status": asset.status,
        "embedding_status": asset.embedding_status,
    }


# =========================================================
# LIST ASSETS
# =========================================================

@router.get("")
def list_assets(
    file_type: Optional[str] = Query(
        None,
        description="image, video, or pdf",
    ),
    limit: int = Query(
        100,
        ge=1,
        le=500,
    ),
    offset: int = Query(
        0,
        ge=0,
    ),
    db: Session = Depends(get_db),
):
    """
    Browse the asset library.

    This endpoint is used when the user has not
    entered a semantic search query yet.
    """

    query = (
        db.query(Asset)
        .filter(
            Asset.status != "duplicate"
        )
    )

    if file_type:
        file_type = file_type.lower()

        if file_type not in {
            "image",
            "video",
            "pdf",
        }:
            raise HTTPException(
                status_code=400,
                detail=(
                    "file_type must be "
                    "image, video, or pdf"
                ),
            )

        query = query.filter(
            Asset.file_type == file_type
        )

    total = query.count()

    assets = (
        query
        .order_by(Asset.id)
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "count": len(assets),
        "total": total,
        "offset": offset,
        "limit": limit,
        "results": [
            asset_to_dict(asset)
            for asset in assets
        ],
    }


# =========================================================
# SINGLE ASSET
# =========================================================

@router.get("/{asset_id}")
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
):
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id)
        .first()
    )

    if asset is None:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    return asset_to_dict(asset)


# =========================================================
# ASSET PREVIEW
# =========================================================

@router.get("/{asset_id}/preview")
def preview_asset(
    asset_id: int,
    db: Session = Depends(get_db),
):
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id)
        .first()
    )

    if asset is None:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    file_path = Path(
        asset.file_path
    )

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Asset file no longer exists",
        )

    if asset.status == "duplicate":
        raise HTTPException(
            status_code=409,
            detail="Asset is marked as duplicate",
        )

    return FileResponse(
        path=str(file_path),
        media_type=asset.mime_type,
        filename=asset.filename,
        content_disposition_type="inline",
    )