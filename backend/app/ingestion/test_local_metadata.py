from app.database.database import (
    SessionLocal,
    init_database,
)

from app.ingestion.local_metadata import (
    rebuild_local_metadata,
)


if __name__ == "__main__":

    init_database()

    db = SessionLocal()

    try:

        print(
            "\nStarting local metadata indexing..."
        )

        stats = rebuild_local_metadata(db)

        print("\n")
        print("=" * 40)
        print("LOCAL METADATA INDEX COMPLETE")
        print("=" * 40)

        print(
            f"Total      : {stats['total']}"
        )

        print(
            f"Indexed    : {stats['indexed']}"
        )

        print(
            f"Skipped    : {stats['skipped']}"
        )

        print(
            f"Duplicates : {stats['duplicates']}"
        )

        print(
            f"Failed     : {stats['failed']}"
        )

    finally:

        db.close()