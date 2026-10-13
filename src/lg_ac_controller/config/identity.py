"""Identidade persistente e não secreta do cliente ThinQ."""

from __future__ import annotations

import os
import uuid
from pathlib import Path


class ClientIdentityError(RuntimeError):
    """Indica falha ao ler ou criar a identidade do cliente."""


def get_or_create_client_id(path: Path | None = None) -> str:
    target = path or _default_client_id_path()
    try:
        if target.is_file():
            existing = target.read_text(encoding="ascii").strip()
            if existing:
                uuid.UUID(existing)
                return existing

        client_id = str(uuid.uuid4())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(client_id, encoding="ascii")
        return client_id
    except (OSError, ValueError) as exc:
        raise ClientIdentityError(
            "Não foi possível preparar a identidade do cliente ThinQ."
        ) from exc


def _default_client_id_path() -> Path:
    local_app_data = os.getenv("LOCALAPPDATA")
    base_dir = Path(local_app_data) if local_app_data else Path.cwd() / ".runtime"
    return base_dir / "LGAcController" / "client_id"
