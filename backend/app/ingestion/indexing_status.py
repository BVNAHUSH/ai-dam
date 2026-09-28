from threading import Lock


class IndexingStatus:
    def __init__(self):
        self._lock = Lock()
        self.reset()

    def reset(self):
        with self._lock:
            self.running = False
            self.total = 0
            self.processed = 0
            self.completed = 0
            self.skipped = 0
            self.duplicate = 0
            self.failed = 0
            self.current_file = None
            self.current_type = None

    def start(self, total: int):
        with self._lock:
            self.running = True
            self.total = total
            self.processed = 0
            self.completed = 0
            self.skipped = 0
            self.duplicate = 0
            self.failed = 0
            self.current_file = None
            self.current_type = None

    def update_current(
        self,
        filename: str,
        media_type: str,
    ):
        with self._lock:
            self.current_file = filename
            self.current_type = media_type

    def record_result(self, result: str):
        with self._lock:
            self.processed += 1

            if result == "completed":
                self.completed += 1
            elif result == "skipped":
                self.skipped += 1
            elif result == "duplicate":
                self.duplicate += 1
            elif result == "failed":
                self.failed += 1

    def finish(self):
        with self._lock:
            self.running = False
            self.current_file = None
            self.current_type = None

    def get(self):
        with self._lock:
            progress = (
                (self.processed / self.total) * 100
                if self.total
                else 0
            )

            return {
                "running": self.running,
                "total": self.total,
                "processed": self.processed,
                "completed": self.completed,
                "skipped": self.skipped,
                "duplicate": self.duplicate,
                "failed": self.failed,
                "current_file": self.current_file,
                "current_type": self.current_type,
                "progress": round(progress, 1),
            }


indexing_status = IndexingStatus()