from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CACHE_DIRS = [
    ROOT / "__pycache__",
    ROOT / ".pytest_cache",
    ROOT / "pytest" / ".pytest_cache",
    ROOT / ".venv" / "__pycache__",
]

CACHE_FILES = [
    ROOT / ".coverage",
    ROOT / ".coverage.*",
]


def clear_cache() -> list[str]:
    removed: list[str] = []

    for path in CACHE_DIRS:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
            removed.append(str(path.relative_to(ROOT)))

    for pattern in CACHE_FILES:
        for path in ROOT.glob(str(pattern.name if pattern.is_absolute() else pattern)):
            if path.is_file():
                path.unlink(missing_ok=True)
                removed.append(str(path.relative_to(ROOT)))

    for path in ROOT.rglob("__pycache__"):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
            removed.append(str(path.relative_to(ROOT)))

    for path in ROOT.rglob(".pytest_cache"):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
            removed.append(str(path.relative_to(ROOT)))

    return removed


if __name__ == "__main__":
    removed = clear_cache()
    if removed:
        print("Removed cache paths:")
        for item in removed:
            print(f"- {item}")
    else:
        print("No cache directories or files found.")
