from pathlib import Path

from app.search.embeddings import CLIPEmbedder
from app.search.faiss_index import FAISSIndex


if __name__ == "__main__":

    project_root = (
        Path(__file__).resolve().parents[3]
    )

    image_folder = (
        project_root
        / "dataset"
        / "images"
    )

    index_path = (
        project_root
        / "data"
        / "images.index.faiss"
    )

    images = sorted(
        image_folder.glob("*.jpg")
    )

    if not images:
        raise RuntimeError(
            "No JPG images found."
        )

    print(
        f"Found {len(images)} images."
    )

    # ---------------------------------------------------------
    # Load model
    # ---------------------------------------------------------

    embedder = CLIPEmbedder()

    # ---------------------------------------------------------
    # Create FAISS index
    # ---------------------------------------------------------

    index = FAISSIndex(
        dimension=512,
        index_path=index_path,
    )

    # ---------------------------------------------------------
    # Generate embeddings
    # ---------------------------------------------------------

    for position, image_path in enumerate(
        images,
        start=1,
    ):

        print(
            f"[{position}/{len(images)}] "
            f"{image_path.name}"
        )

        vector = embedder.embed_image(
            image_path
        )

        # For this initial test we use the
        # image position as the identifier.
        index.add(
            asset_id=position,
            vector=vector,
        )

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------

    index.save()

    print("\n==============================")
    print("IMAGE INDEX COMPLETE")
    print("==============================")

    print(
        "Images indexed:",
        len(images),
    )

    print(
        "FAISS vectors:",
        index.index.ntotal,
    )

    print(
        "Index:",
        index_path,
    )