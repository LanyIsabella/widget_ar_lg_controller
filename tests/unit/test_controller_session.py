import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from lg_ac_controller.config.settings import ControllerSettings
from lg_ac_controller.services.controller_session import (
    ControllerSession,
    CredentialNotConfigured,
)
from lg_ac_controller.services.ac_service import ACService


class EmptyCredentialStore:
    def get_pat(self):
        return None


class CredentialStoreWithPat:
    def get_pat(self):
        return "pat-kept-out-of-logs"


def test_session_requires_pat():
    with pytest.raises(CredentialNotConfigured):
        asyncio.run(
            ControllerSession.create(
                ControllerSettings(client_id="client-1"), EmptyCredentialStore()
            )
        )


def test_session_wires_pat_settings_and_service():
    fake_provider = object()
    factory = AsyncMock(return_value=fake_provider)
    settings = ControllerSettings(client_id="client-1", country="BR")

    with patch(
        "lg_ac_controller.services.controller_session.ThinQProvider.create",
        factory,
    ):
        session = asyncio.run(
            ControllerSession.create(settings, CredentialStoreWithPat())
        )

    assert isinstance(session.ac_service, ACService)
    factory.assert_awaited_once_with(
        access_token="pat-kept-out-of-logs",
        country_code="BR",
        client_id="client-1",
        read_attempts=2,
        retry_backoff_seconds=0.5,
    )
