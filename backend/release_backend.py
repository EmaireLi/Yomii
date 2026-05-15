from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn


def _runtime_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _configure_release_env() -> None:
    runtime_dir = _runtime_dir()
    data_dir = runtime_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("USER_DATABASE_BACKEND", "sqlite")
    os.environ.setdefault("SQLITE_DATABASE_PATH", str((data_dir / "dictionary.db").resolve()))
    os.environ.setdefault("USER_SQLITE_DATABASE_PATH", str((data_dir / "user_data.db").resolve()))
    os.environ.setdefault("ENABLE_ESSAY_EVALUATION", "false")
    os.environ.setdefault("ENABLE_DEFAULT_AUTO_LOGIN", "true")
    os.environ.setdefault("DEFAULT_RELEASE_USERNAME", "丰川祥子")
    os.environ.setdefault("DEFAULT_RELEASE_PHONE", "18800000000")
    os.environ.setdefault("DEEPSEEK_API_KEY", "")
    os.environ.setdefault("DEEPSEEK_BASE_URL", "")
    os.environ.setdefault("DEEPSEEK_MODEL", "")
    os.environ.setdefault("ESSAY_SCORE_MODEL_URL", "")
    os.environ.setdefault("ESSAY_REVISION_MODEL_URL", "")


def main() -> int:
    _configure_release_env()
    from app.main import app

    port = int(os.getenv("YOMII_BACKEND_PORT", "8000"))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())