"""Erros seguros e classificáveis da integração externa."""

from __future__ import annotations

import asyncio
from enum import StrEnum
from collections.abc import Awaitable, Callable


class ProviderErrorKind(StrEnum):
    AUTHENTICATION = "authentication"
    NETWORK = "network"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class ProviderError(RuntimeError):
    """Erro sem detalhes sensíveis do transporte ou do SDK."""

    def __init__(
        self, operation: str, kind: ProviderErrorKind, message: str
    ) -> None:
        super().__init__(message)
        self.operation = operation
        self.kind = kind


class ProviderAuthenticationError(ProviderError):
    def __init__(self, operation: str, message: str = "A autenticação LG foi recusada.") -> None:
        super().__init__(operation, ProviderErrorKind.AUTHENTICATION, message)


class ProviderTimeoutError(ProviderError):
    def __init__(self, operation: str) -> None:
        super().__init__(
            operation,
            ProviderErrorKind.TIMEOUT,
            f"A operação LG {operation!r} excedeu o tempo limite.",
        )


class ProviderNetworkError(ProviderError):
    def __init__(self, operation: str) -> None:
        super().__init__(
            operation,
            ProviderErrorKind.NETWORK,
            f"Não foi possível comunicar com a API LG durante {operation!r}.",
        )


def classify_provider_exception(exc: BaseException, operation: str) -> ProviderError:
    """Convert known transport/auth failures without copying raw SDK text."""

    if isinstance(exc, (asyncio.TimeoutError, TimeoutError)):
        return ProviderTimeoutError(operation)

    try:
        from aiohttp import ClientError
    except ImportError:
        ClientError = ()  # type: ignore[assignment]
    if ClientError and isinstance(exc, ClientError):
        return ProviderNetworkError(operation)

    # The SDK exposes API error codes inconsistently across versions. Only the
    # observed ThinQ access-denied code is classified as authentication; all
    # other unknown errors remain deliberately generic.
    if str(getattr(exc, "code", "")) == "1309":
        return ProviderAuthenticationError(operation)

    return ProviderError(
        operation,
        ProviderErrorKind.UNKNOWN,
        f"Falha inesperada na operação LG {operation!r}.",
    )


async def invoke_provider(
    operation: str,
    call: Callable[[], Awaitable[Any]],
    *,
    attempts: int = 1,
    backoff_seconds: float = 0.0,
) -> Any:
    """Run an SDK operation with bounded retries for read-only transport errors."""

    if attempts < 1:
        raise ValueError("attempts deve ser pelo menos 1.")
    if backoff_seconds < 0:
        raise ValueError("backoff_seconds não pode ser negativo.")

    for attempt in range(attempts):
        try:
            return await call()
        except ProviderError:
            raise
        except Exception as exc:  # noqa: BLE001 - integration boundary
            error = classify_provider_exception(exc, operation)
            retryable = error.kind in {
                ProviderErrorKind.NETWORK,
                ProviderErrorKind.TIMEOUT,
            }
            if not retryable or attempt == attempts - 1:
                raise error from exc
            await asyncio.sleep(backoff_seconds * (2**attempt))

    raise AssertionError("A operação do provedor terminou sem resultado.")
