from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.search.service import SearchService


router = APIRouter(
    prefix="/api/search",
    tags=["Search"],
)


@router.get("")
def semantic_search(
    q: str = Query(
        ...,
        min_length=1,
        description="Natural language search query",
    ),
    top_k: int = Query(
        20,
        ge=1,
        le=100,
    ),
    file_type: Optional[str] = Query(
        None,
        description="image, video, or pdf",
    ),
    db: Session = Depends(get_db),
):
    """
    Search the DAM using natural language.
    """

    try:

        service = SearchService(
            db=db
        )

        results = service.search(
            query=q,
            top_k=top_k,
            file_type=file_type,
        )

        return {
            "query": q,
            "count": len(results),
            "results": results,
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except RuntimeError as exc:

        raise HTTPException(
            status_code=503,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {exc}",
        )