from app.ingestion.scanner import scan_dataset


if __name__ == "__main__":

    counts = {
        "image": 0,
        "video": 0,
        "pdf": 0,
    }

    print("\nScanning dataset...\n")

    for file_path, media_type in scan_dataset():

        counts[media_type] += 1

        print(
            f"[{media_type.upper():5}] "
            f"{file_path}"
        )

    print("\n==============================")
    print("SCAN COMPLETE")
    print("==============================")

    print(f"Images : {counts['image']}")
    print(f"Videos : {counts['video']}")
    print(f"PDFs   : {counts['pdf']}")
    print(f"Total  : {sum(counts.values())}")