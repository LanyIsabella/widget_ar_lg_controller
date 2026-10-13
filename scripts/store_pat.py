"""Armazena um PAT informado pelo usuário no cofre de credenciais do Windows."""

from __future__ import annotations

import getpass
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lg_ac_controller.config.credentials import WindowsCredentialStore  # noqa: E402


def main() -> int:
    pat = getpass.getpass("PAT LG ThinQ Connect (não será exibido): ").strip()
    if not pat:
        print("Nenhum PAT foi informado.", file=sys.stderr)
        return 2
    WindowsCredentialStore().set_pat(pat)
    print("PAT armazenado no Windows Credential Manager; o valor não foi exibido.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
