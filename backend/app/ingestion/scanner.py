from pathlib import Path
from typing import Iterator

from app.config import (
    DATASET_PATH,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    PDF_EXTENSIONS,
)


def get_file_type(file_path: Path) -> str | None:
    """Return the supported media type for a file."""

    extension = file_path.suffix.lower()

    if extension in IMAGE_EXTENSIONS:
        return "image"

    if extension in VIDEO_EXTENSIONS:
        return "video"

    if extension in PDF_EXTENSIONS:
        return "pdf"

    return None


def scan_dataset(
    dataset_path: Path = DATASET_PATH,
) -> Iterator[tuple[Path, str]]:
    """
    Recursively scan the dataset directory.

    Yields:
        (file_path, media_type)
    """

    if not dataset_path.exists():
        return

    for file_path in dataset_path.rglob("*"):

        if not file_path.is_file():
            continue

        media_type = get_file_type(file_path)

        if media_type is None:
            continue

        yield file_path, media_type