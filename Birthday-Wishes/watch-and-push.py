"""Watch the repository and push local changes to its Git remote."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from threading import Lock, Timer

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class RepositoryWatcher(FileSystemEventHandler):
    def __init__(self, repository: Path, debounce_seconds: float) -> None:
        self.repository = repository
        self.debounce_seconds = debounce_seconds
        self._timer: Timer | None = None
        self._timer_lock = Lock()
        self._push_lock = Lock()

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory or self._is_ignored(Path(event.src_path)):
            return

        with self._timer_lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = Timer(self.debounce_seconds, self._sync_changes)
            self._timer.daemon = True
            self._timer.start()

        print(f"Change detected; waiting {self.debounce_seconds:g} seconds before push.", flush=True)

    def _is_ignored(self, path: Path) -> bool:
        try:
            relative_path = path.resolve().relative_to(self.repository.resolve())
        except ValueError:
            return True

        ignored_parts = {".git", "__pycache__", ".pytest_cache"}
        return any(part in ignored_parts for part in relative_path.parts)

    def _sync_changes(self) -> None:
        if not self._push_lock.acquire(blocking=False):
            print("A push is already in progress; waiting for the next change.", flush=True)
            return

        try:
            if not self._run_git("status", "--porcelain", "--untracked-files=all").stdout.strip():
                return

            branch = self._run_git("branch", "--show-current").stdout.strip()
            if not branch:
                raise RuntimeError("The repository is in detached HEAD state.")

            self._run_git("add", "--all")
            self._run_git("commit", "-m", "Automatic local sync")
            self._run_git("push", "origin", branch)
            print(f"Pushed local changes to origin/{branch}.", flush=True)
        except (RuntimeError, subprocess.CalledProcessError) as error:
            print(f"Automatic push failed: {error}", file=sys.stderr, flush=True)
        finally:
            self._push_lock.release()

    def _run_git(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=self.repository,
            check=True,
            text=True,
            capture_output=True,
        )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--debounce",
        type=float,
        default=10,
        help="Seconds to wait after the last file change before pushing (default: 10).",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    repository = Path(__file__).resolve().parent
    handler = RepositoryWatcher(repository, arguments.debounce)
    observer = Observer()
    observer.schedule(handler, str(repository), recursive=True)
    observer.start()

    print(f"Watching {repository}", flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    try:
        while observer.is_alive():
            observer.join(1)
    except KeyboardInterrupt:
        print("Stopping watcher.", flush=True)
    finally:
        observer.stop()
        observer.join()
        handler._timer.cancel() if handler._timer is not None else None

    return 0


if __name__ == "__main__":
    raise SystemExit(main())