import asyncio
import os

import pytest


@pytest.mark.integration
def test_live_thinq_read_is_opt_in():
    """Run only with LG_THINQ_LIVE=1 and a PAT supplied by the environment."""

    if os.getenv("LG_THINQ_LIVE") != "1":
        pytest.skip("Teste real desabilitado; use LG_THINQ_LIVE=1 explicitamente.")

    from aiohttp import ClientSession
    from thinqconnect.thinq_api import ThinQApi

    async def read_devices():
        async with ClientSession() as session:
            api = ThinQApi(
                session=session,
                access_token=os.environ["LG_THINQ_PAT"],
                country_code=os.getenv("LG_THINQ_COUNTRY", "BR"),
                client_id=os.environ["LG_THINQ_CLIENT_ID"],
            )
            return await api.async_get_device_list(timeout=15)

    devices = asyncio.run(read_devices())
    assert isinstance(devices, list)
