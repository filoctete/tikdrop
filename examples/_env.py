"""Tiny dependency-free .env loader for local scripts/examples. Not part of the tikdrop package
itself - production code should get secrets from the real environment, not parse .env files.
"""

from pathlib import Path


def load_dotenv_if_present() -> None:
    import os

    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())
