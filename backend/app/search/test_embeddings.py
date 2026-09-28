from pathlib import Path

from app.search.embeddings import CLIPEmbedder


if __name__ == "__main__":

    image_folder = (
        Path(__file__).resolve().parents[3]
        / "dataset"
        / "images"
    )

    images = list(
        image_folder.glob("*.jpg")
    )

    if not images:
        raise RuntimeError(
            "No JPG images found."
        )

    image = images[0]

    print("\nInitializing embedder...\n")

    embedder = CLIPEmbedder()

    print("\nEmbedding image:")
    print(image.name)

    image_vector = embedder.embed_image(
        image
    )

    print(
        "\nImage embedding:"
    )

    print(
        "Shape:",
        image_vector.shape,
    )

    print(
        "Data type:",
        image_vector.dtype,
    )

    print(
        "First 10 values:",
        image_vector[:10],
    )

    # ---------------------------------------------------------
    # Test text query
    # ---------------------------------------------------------

    query = "construction workers at a building site"

    print(
        f"\nEmbedding query: "
        f'"{query}"'
    )

    text_vector = embedder.embed_text(
        query
    )

    print(
        "Text embedding shape:",
        text_vector.shape,
    )

    # Because both vectors are normalized,
    # their dot product is cosine similarity.

    similarity = float(
        image_vector @ text_vector
    )

    print(
        "\nImage ↔ query similarity:",
        similarity,
    )