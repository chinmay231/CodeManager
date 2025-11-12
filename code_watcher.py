from __future__ import annotations

import time
from pathlib import Path
from threading import Event
from typing import Callable, List

from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler, FileSystemEvent


class _BatchingHandler(FileSystemEventHandler):
    def __init__(self, root: Path, exclude_dirs, exclude_file_regexes, debounce_ms: int, on_batch: Callable[[List[str]], None]):
        self.root = Path(root)
        self.exclude_dirs = set([d.strip() for d in (exclude_dirs or [])])
        self.exclude_file_regexes = exclude_file_regexes or []
        self.debounce_ms = max(50, int(debounce_ms))
        self.on_batch = on_batch
        self._changes = set()
        self._last_emit = 0

    def _relevant(self, p: Path) -> bool:
        try:
            rel = p.relative_to(self.root)
        except ValueError:
            return False
        for part in rel.parts:
            if part in self.exclude_dirs:
                return False
        if p.is_file():
            s = str(p)
            for rx in self.exclude_file_regexes:
                if rx.search(s):
                    return False
        return True

    def _maybe_emit(self):
        now = int(time.time() * 1000)
        if self._changes and (now - self._last_emit) >= self.debounce_ms:
            paths = sorted(self._changes)
            self._changes.clear()
            self._last_emit = now
            try:
                self.on_batch(paths)
            except Exception:
                pass

    def on_any_event(self, event: FileSystemEvent):
        p = Path(event.src_path)
        if self._relevant(p):
            self._changes.add(str(p))
        self._maybe_emit()


def _pick_observer(root_path: Path):
    rp = str(root_path)
    if rp.startswith("/mnt/"):
        return PollingObserver()
    return Observer()


class DirectoryWatcher:
    def __init__(self, root: Path, exclude_dirs=None, exclude_file_regexes=None, debounce_ms: int = 400, on_batch: Callable[[List[str]], None] = None):
        self.root = Path(root)
        self.exclude_dirs = exclude_dirs or []
        self.exclude_file_regexes = exclude_file_regexes or []
        self.debounce_ms = debounce_ms
        self.on_batch = on_batch or (lambda paths: None)
        self._observer: Observer | None = None

    def start(self):
        handler = _BatchingHandler(
            root=self.root,
            exclude_dirs=self.exclude_dirs,
            exclude_file_regexes=self.exclude_file_regexes,
            debounce_ms=self.debounce_ms,
            on_batch=self.on_batch,
        )
        self._observer = _pick_observer(self.root)
        self._observer.schedule(handler, str(self.root), recursive=True)
        self._observer.start()

    def stop(self):
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
