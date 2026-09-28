from pathlib import Path

import cv2
import fitz
from PIL import Image
from sqlalchemy.orm import Session

from app.database.models import Asset
from app.ingestion.hasher import calculate_sha256
from app.ingestion.scanner import scan_dataset


def extract_pdf_text(file_path: Path) -> str:
    """
    Extract text from all readable pages of a PDF.
    """
    document = fitz.open(file_path)
    pages = []

    try:
        for page in document:
            text = page.get_text()

            if text and text.strip():
                pages.append(text.strip())

    finally:
        document.close()

    return "\n\n".join(pages)


def extract_video_metadata(file_path: Path) -> dict:
    """
    Extract basic technical metadata from a video.
    """
    capture = cv2.VideoCapture(str(file_path))

    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {file_path}")

    try:
        fps = capture.get(cv2.CAP_PROP_FPS)
        frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT)

        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if fps and fps > 0:
            duration = frame_count / fps
        else:
            duration = 0

        return {
            "width": width,
            "height": height,
            "duration": duration,
        }

    finally:
        capture.release()


def process_local_metadata(
    db: Session,
    file_path: Path,
    media_type: str,
):
    """
    Register or update one asset in SQLite.

    The function:
    - calculates SHA-256
    - detects duplicates
    - stores file metadata
    - extracts image dimensions
    - extracts video dimensions/duration
    - extracts PDF text
    - skips truly unchanged and complete files
    """

    resolved_path = str(file_path.resolve())
    stat = file_path.stat()

    # ---------------------------------------------------------
    # Check whether this file already exists in the database
    # ---------------------------------------------------------

    existing = (
        db.query(Asset)
        .filter(Asset.file_path == resolved_path)
        .first()
    )

    # ---------------------------------------------------------
    # Calculate current file hash
    # ---------------------------------------------------------

    file_hash = calculate_sha256(file_path)

    # ---------------------------------------------------------
    # Determine whether the existing metadata is complete
    # ---------------------------------------------------------

    metadata_complete = True

    if existing:

        if media_type == "image":
            metadata_complete = (
                existing.width is not None
                and existing.height is not None
            )

        elif media_type == "video":
            metadata_complete = (
                existing.width is not None
                and existing.height is not None
                and existing.duration is not None
            )

        elif media_type == "pdf":
            metadata_complete = bool(
                existing.extracted_text
                and existing.extracted_text.strip()
            )

        # -----------------------------------------------------
        # If file is unchanged AND metadata is complete,
        # there is nothing to do.
        # -----------------------------------------------------

        unchanged = (
            existing.file_size == stat.st_size
            and existing.modified_time == stat.st_mtime
            and existing.sha256 == file_hash
        )

        if unchanged and metadata_complete:
            return "skipped"

    # ---------------------------------------------------------
    # Duplicate detection
    #
    # Same SHA-256 = same file content.
    # ---------------------------------------------------------

    duplicate = (
        db.query(Asset)
        .filter(
            Asset.sha256 == file_hash,
            Asset.file_path != resolved_path,
        )
        .first()
    )

    # ---------------------------------------------------------
    # Create new database record if necessary
    # ---------------------------------------------------------

    if existing is None:

        existing = Asset(
            file_path=resolved_path,
            filename=file_path.name,
            file_type=media_type,
            file_size=stat.st_size,
            sha256=file_hash,
            modified_time=stat.st_mtime,
            status="pending",
            embedding_status="pending",
        )

        db.add(existing)

    else:

        # -----------------------------------------------------
        # File changed since previous indexing
        # -----------------------------------------------------

        existing.filename = file_path.name
        existing.file_type = media_type
        existing.file_size = stat.st_size
        existing.sha256 = file_hash
        existing.modified_time = stat.st_mtime

        # AI processing will need to happen again
        existing.status = "pending"
        existing.embedding_status = "pending"

        existing.error_message = None

    # ---------------------------------------------------------
    # Handle duplicate
    # ---------------------------------------------------------

    if duplicate:

        existing.status = "duplicate"

        existing.error_message = (
            f"Duplicate of asset ID {duplicate.id}"
        )

        db.commit()

        return "duplicate"

    # ---------------------------------------------------------
    # IMAGE METADATA
    # ---------------------------------------------------------

    if media_type == "image":

        try:

            with Image.open(file_path) as image:

                existing.width = image.width
                existing.height = image.height

                # Optional MIME type
                if image.format:
                    existing.mime_type = (
                        Image.MIME.get(image.format)
                    )

        except Exception as exc:

            existing.status = "failed"

            existing.error_message = (
                f"Image metadata error: {exc}"
            )

            db.commit()

            return "failed"

    # ---------------------------------------------------------
    # VIDEO METADATA
    # ---------------------------------------------------------

    elif media_type == "video":

        try:

            metadata = extract_video_metadata(file_path)

            existing.width = metadata["width"]
            existing.height = metadata["height"]
            existing.duration = metadata["duration"]

            existing.mime_type = (
                f"video/{file_path.suffix.lower().lstrip('.')}"
            )

        except Exception as exc:

            existing.status = "failed"

            existing.error_message = (
                f"Video metadata error: {exc}"
            )

            db.commit()

            return "failed"

    # ---------------------------------------------------------
    # PDF METADATA + TEXT EXTRACTION
    # ---------------------------------------------------------

    elif media_type == "pdf":

        try:

            extracted_text = extract_pdf_text(file_path)

            existing.extracted_text = extracted_text

            existing.mime_type = "application/pdf"

        except Exception as exc:

            existing.status = "failed"

            existing.error_message = (
                f"PDF extraction error: {exc}"
            )

            db.commit()

            return "failed"

    # ---------------------------------------------------------
    # Unsupported media type
    # ---------------------------------------------------------

    else:

        existing.status = "failed"

        existing.error_message = (
            f"Unsupported media type: {media_type}"
        )

        db.commit()

        return "failed"

    # ---------------------------------------------------------
    # Metadata successfully processed
    #
    # AI understanding is intentionally NOT performed here.
    # That happens later in the AI indexing pipeline.
    # ---------------------------------------------------------

    existing.status = "pending"
    existing.embedding_status = "pending"

    db.commit()

    return "indexed"


def rebuild_local_metadata(db: Session):
    """
    Scan the complete dataset and synchronize local metadata
    with the SQLite database.

    This operation is incremental:
    - unchanged files -> skipped
    - new files -> indexed
    - modified files -> re-indexed
    - duplicate files -> marked duplicate
    - corrupted/unsupported files -> failed
    """

    stats = {
        "total": 0,
        "indexed": 0,
        "skipped": 0,
        "duplicates": 0,
        "failed": 0,
    }

    # ---------------------------------------------------------
    # Scan dataset
    # ---------------------------------------------------------

    for file_path, media_type in scan_dataset():

        stats["total"] += 1

        print(
            f"\n[{stats['total']}] "
            f"{media_type.upper():5} "
            f"{file_path.name}"
        )

        try:

            result = process_local_metadata(
                db=db,
                file_path=file_path,
                media_type=media_type,
            )

            if result == "indexed":

                stats["indexed"] += 1

                print("    ✓ metadata indexed")

            elif result == "skipped":

                stats["skipped"] += 1

                print("    → unchanged, skipped")

            elif result == "duplicate":

                stats["duplicates"] += 1

                print("    → duplicate")

            elif result == "failed":

                stats["failed"] += 1

                print("    ✗ failed")

        except Exception as exc:

            stats["failed"] += 1

            print(
                f"    ✗ unexpected failure: {exc}"
            )

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    print("\n" + "=" * 45)
    print("LOCAL METADATA INDEX COMPLETE")
    print("=" * 45)

    print(f"Total      : {stats['total']}")
    print(f"Indexed    : {stats['indexed']}")
    print(f"Skipped    : {stats['skipped']}")
    print(f"Duplicates : {stats['duplicates']}")
    print(f"Failed     : {stats['failed']}")

    return stats