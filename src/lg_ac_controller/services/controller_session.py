"""Composição da integração e dos serviços sem dependência da UI."""

from __future__ import annotations

from dataclasses import dataclass

from lg_ac_controller.config.credentials import CredentialStore
from lg_ac_controller.config.settings import ControllerSettings
from lg_ac_controller.integrations.thinq_provider import ThinQProvider
from lg_ac_controller.services.ac_service import ACService


class CredentialNotConfigured(RuntimeError):
    """Indica que nenhum PAT foi encontrado no cofre configurado."""


@dataclass(slots=True)
class ControllerSession:
    """Owns the provider and exposes the application service boundary."""

    provider: ThinQProvider
    ac_service: ACService

    @classmethod
    async def create(
        cls,
        settings: ControllerSettings,
        credential_store: CredentialStore,
    ) -> "ControllerSession":
        pat = credential_store.get_pat()
        if not pat:
            raise CredentialNotConfigured(
                "Nenhum PAT LG foi encontrado no Windows Credential Manager."
            )
        if not settings.client_id:
            raise ValueError("client_id deve ser configurado antes de criar a sessão.")

        provider = await ThinQProvider.create(
            access_token=pat,
            country_code=settings.country,
            client_id=settings.client_id,
            read_attempts=settings.read_retry_attempts,
            retry_backoff_seconds=settings.retry_backoff_seconds,
        )
        return cls(provider=provider, ac_service=ACService(provider))

    async def close(self) -> None:
        await self.provider.close()

    async def __aenter__(self) -> "ControllerSession":
        return self

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        await self.close()
