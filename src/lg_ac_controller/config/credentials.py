"""Abstração para armazenar PAT fora dos arquivos da aplicação."""

from __future__ import annotations

from typing import Protocol


class CredentialStore(Protocol):
    def get_pat(self) -> str | None:
        ...

    def set_pat(self, pat: str) -> None:
        ...

    def delete_pat(self) -> None:
        ...


class WindowsCredentialStore:
    """Usa o backend do keyring configurado para o Windows."""

    def __init__(self, service_name: str = "LGAcController", username: str = "thinq-pat") -> None:
        self._service_name = service_name
        self._username = username

    def get_pat(self) -> str | None:
        import keyring

        return keyring.get_password(self._service_name, self._username)

    def set_pat(self, pat: str) -> None:
        if not pat.strip():
            raise ValueError("O PAT não pode ser vazio.")
        import keyring

        keyring.set_password(self._service_name, self._username, pat.strip())

    def delete_pat(self) -> None:
        import keyring

        try:
            keyring.delete_password(self._service_name, self._username)
        except keyring.errors.PasswordDeleteError:
            pass
