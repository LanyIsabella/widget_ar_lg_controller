"""Diagnóstico e teste controlado da integração LG ThinQ Connect.

Uso:
    python scripts/diagnose_thinq.py --country BR

O script não salva o PAT. Ele permanece somente leitura por padrão; o teste
físico de desligamento exige as opções explícitas de autorização.
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lg_ac_controller.diagnostic import (  # noqa: E402
    device_field,
    normalize_device_list,
    observed_attributes,
    profile_supports_writable_enum,
    redact_payload,
    select_air_conditioner,
    summarize_device,
)
from lg_ac_controller.config.credentials import WindowsCredentialStore  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Consulta um AC LG e, com confirmação explícita, testa desligamento."
    )
    parser.add_argument(
        "--country",
        default=os.getenv("LG_THINQ_COUNTRY", "BR"),
        help="Código do país da conta LG (padrão: BR ou LG_THINQ_COUNTRY).",
    )
    parser.add_argument(
        "--token-env",
        default="LG_THINQ_PAT",
        help="Nome da variável de ambiente com o PAT (padrão: LG_THINQ_PAT).",
    )
    parser.add_argument(
        "--client-id",
        default=os.getenv("LG_THINQ_CLIENT_ID"),
        help="Client ID persistente opcional; por padrão um UUID novo é gerado nesta execução.",
    )
    selector = parser.add_argument_group("seleção do dispositivo")
    selector_choice = selector.add_mutually_exclusive_group()
    selector_choice.add_argument("--device-id", help="ID exato do ar-condicionado.")
    selector_choice.add_argument("--device-alias", help="Alias exato, ignorando maiúsculas/minúsculas.")
    selector_choice.add_argument(
        "--device-index",
        type=int,
        help="Posição 1-based entre os ar-condicionados encontrados.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Timeout de cada chamada HTTP em segundos (padrão: 15).",
    )
    parser.add_argument(
        "--hide-device-id",
        action="store_true",
        help="Redige IDs de dispositivo no relatório impresso.",
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Lista dispositivos e não consulta perfil/estado.",
    )
    control = parser.add_mutually_exclusive_group()
    control.add_argument(
        "--power-off",
        action="store_true",
        help="Envia um único comando de desligamento; exige --confirm-physical-action.",
    )
    parser.add_argument(
        "--confirm-physical-action",
        action="store_true",
        help="Confirma que uma ação física autorizada pode ser enviada.",
    )
    return parser


def get_token(token_env: str) -> str:
    load_dotenv_file()
    token = os.getenv(token_env)
    if not token and token_env == "LG_THINQ_PAT":
        token = os.getenv("PAT_LG")
    if token:
        return token

    # Prefer the OS credential store before asking for an interactive PAT.
    # Backend errors are intentionally ignored so the read-only diagnostic can
    # still be used on a machine without a configured keyring backend.
    try:
        stored_token = WindowsCredentialStore().get_pat()
    except Exception:  # noqa: BLE001 - optional platform credential backend
        stored_token = None
    if stored_token:
        return stored_token

    token = getpass.getpass("PAT LG ThinQ Connect (não será salvo): ").strip()
    if not token:
        raise ValueError("Nenhum PAT foi informado.")
    return token


def get_client_id(explicit_client_id: str | None) -> str:
    """Return a stable non-secret client ID, as required by the API client."""

    if explicit_client_id:
        return explicit_client_id

    configured_client_id = os.getenv("LG_THINQ_CLIENT_ID")
    if configured_client_id:
        return configured_client_id

    local_app_data = os.getenv("LOCALAPPDATA")
    base_dir = Path(local_app_data) if local_app_data else ROOT / ".runtime"
    client_id_path = base_dir / "LGAcController" / "client_id"
    try:
        if client_id_path.is_file():
            saved_client_id = client_id_path.read_text(encoding="ascii").strip()
            if saved_client_id:
                return saved_client_id

        client_id = str(uuid.uuid4())
        client_id_path.parent.mkdir(parents=True, exist_ok=True)
        client_id_path.write_text(client_id, encoding="ascii")
        return client_id
    except OSError:
        # A read-only profile should not prevent a diagnostic attempt.
        return str(uuid.uuid4())


def load_dotenv_file(path: Path = ROOT / ".env") -> None:
    """Load simple KEY=VALUE entries without exposing or persisting secrets."""

    if not path.is_file():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, separator, value = line.partition("=")
        if not separator or not key.strip():
            continue
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


async def collect_report(args: argparse.Namespace, token: str) -> dict[str, Any]:
    try:
        from aiohttp import ClientSession
        from thinqconnect.thinq_api import ThinQApi
    except ImportError as exc:
        raise RuntimeError(
            "Dependências ausentes. Execute: python -m pip install -e \".[dev]\""
        ) from exc

    country = args.country.upper()
    client_id = get_client_id(args.client_id)

    async with ClientSession() as session:
        api = ThinQApi(
            session=session,
            access_token=token,
            country_code=country,
            client_id=client_id,
        )
        raw_devices = await api.async_get_device_list(timeout=args.timeout)
        devices = normalize_device_list(raw_devices)
        reveal_device_ids = not args.hide_device_id
        if args.list_only:
            return {
                "diagnostic": {
                    "mode": "read_only",
                    "provider": "LG ThinQ Connect",
                    "transport": "cloud_api",
                    "country": country,
                    "client_id": client_id,
                    "authentication": {
                        "method": "personal_access_token",
                        "verified_by": "device_list_request",
                    },
                },
                "devices": [
                    summarize_device(device, reveal_device_id=reveal_device_ids)
                    for device in devices
                ],
            }
        selected = select_air_conditioner(
            devices,
            device_id=args.device_id,
            alias=args.device_alias,
            index=args.device_index,
        )
        selected_id = device_field(selected, "deviceId")
        if not selected_id:
            raise ValueError("O dispositivo selecionado não possui deviceId na resposta da API.")

        profile = await api.async_get_device_profile(
            device_id=selected_id,
            timeout=args.timeout,
        )
        state = await api.async_get_device_status(
            device_id=selected_id,
            timeout=args.timeout,
        )

        report = {
            "diagnostic": {
                "mode": "read_only" if not args.power_off else "authorized_control_test",
                "provider": "LG ThinQ Connect",
                "transport": "cloud_api",
                "country": country,
                "client_id": client_id,
                "authentication": {
                    "method": "personal_access_token",
                    "verified_by": "device_list_request",
                },
            },
            "devices": [
                summarize_device(device, reveal_device_id=reveal_device_ids)
                for device in devices
            ],
            "selected_device": summarize_device(
                selected, reveal_device_id=reveal_device_ids
            ),
            "capabilities": redact_payload(
                profile, reveal_device_ids=reveal_device_ids
            ),
            "state": redact_payload(state, reveal_device_ids=reveal_device_ids),
            "observed_attributes": observed_attributes(state),
        }

        if not args.power_off:
            return report
        if not args.confirm_physical_action:
            raise ValueError(
                "--power-off exige --confirm-physical-action para enviar uma ação física."
            )
        if observed_attributes(state).get("airConOperationMode") != "POWER_ON":
            raise ValueError(
                "O estado confirmado antes do teste não é POWER_ON; nenhum comando foi enviado."
            )
        if not profile_supports_writable_enum(
            profile, "operation", "airConOperationMode", "POWER_OFF"
        ):
            raise ValueError(
                "O perfil do modelo não declara POWER_OFF como comando gravável."
            )

        control_response = await api.async_post_device_control(
            device_id=selected_id,
            payload={"operation": {"airConOperationMode": "POWER_OFF"}},
            timeout=args.timeout,
        )
        verification_state = None
        verification_attempts = 0
        for attempt in range(1, 7):
            verification_attempts = attempt
            await asyncio.sleep(2 if attempt > 1 else 1)
            verification_state = await api.async_get_device_status(
                device_id=selected_id,
                timeout=args.timeout,
            )
            if observed_attributes(verification_state).get("airConOperationMode") == "POWER_OFF":
                break

        confirmed = (
            observed_attributes(verification_state or {}).get("airConOperationMode")
            == "POWER_OFF"
        )
        report["diagnostic"]["mode"] = "authorized_control_test"
        report["state_before"] = report.pop("state")
        report["control"] = {
            "command": "POWER_OFF",
            "sent": True,
            "confirmed": confirmed,
            "verification_attempts": verification_attempts,
            "response": redact_payload(
                control_response, reveal_device_ids=reveal_device_ids
            ),
        }
        report["state"] = redact_payload(
            verification_state, reveal_device_ids=reveal_device_ids
        )
        report["observed_attributes"] = observed_attributes(verification_state)
        return report


async def async_main(args: argparse.Namespace) -> int:
    try:
        token = get_token(args.token_env)
        report = await collect_report(args, token)
    except Exception as exc:  # noqa: BLE001 - boundary of a diagnostic CLI
        error_type = type(exc).__name__
        code = getattr(exc, "code", None)
        if code == "1309":
            print(
                "A LG recusou o acesso à API ThinQ Connect (1309 / NOT_ALLOWED_API_AGAIN). "
                "Verifique no portal se o PAT está ativo e autorizado para ThinQ Connect, "
                "se o país da conta é BR e se os termos necessários foram aceitos. "
                "Não compartilhe o PAT; evite várias tentativas consecutivas.",
                file=sys.stderr,
            )
        else:
            print(f"Falha no diagnóstico ({error_type}): {exc}", file=sys.stderr)
        return 2

    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    if report.get("control", {}).get("sent") and not report["control"].get("confirmed"):
        return 3
    return 0


def main() -> int:
    return asyncio.run(async_main(build_parser().parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
