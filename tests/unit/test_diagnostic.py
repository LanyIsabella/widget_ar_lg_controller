from lg_ac_controller.diagnostic import (
    AIR_CONDITIONER_TYPE,
    device_field,
    observed_attributes,
    profile_supports_writable_enum,
    redact_payload,
    select_air_conditioner,
)


def device(device_id: str, alias: str, device_type: str = AIR_CONDITIONER_TYPE) -> dict:
    return {
        "deviceId": device_id,
        "deviceType": device_type,
        "modelName": "LG AC",
        "alias": alias,
    }


def test_selects_single_air_conditioner_without_guessing_other_types() -> None:
    selected = select_air_conditioner(
        [device("ac-1", "Sala"), device("fridge-1", "Cozinha", "DEVICE_REFRIGERATOR")]
    )
    assert selected["deviceId"] == "ac-1"


def test_reads_current_nested_device_info_shape() -> None:
    nested = {"deviceId": "ac-1", "deviceInfo": {"deviceType": AIR_CONDITIONER_TYPE}}
    assert device_field(nested, "deviceType") == AIR_CONDITIONER_TYPE
    assert select_air_conditioner([nested])["deviceId"] == "ac-1"


def test_requires_selector_when_multiple_air_conditioners_exist() -> None:
    try:
        select_air_conditioner([device("ac-1", "Sala"), device("ac-2", "Quarto")])
    except ValueError as exc:
        assert "--device-index" in str(exc)
    else:
        raise AssertionError("A seleção ambígua deveria falhar")


def test_selects_alias_case_insensitively() -> None:
    selected = select_air_conditioner([device("ac-1", "Sala")], alias="sAlA")
    assert selected["deviceId"] == "ac-1"


def test_redacts_token_like_fields_recursively() -> None:
    payload = {"accessToken": "secret", "nested": {"authorization": "bearer secret"}}
    redacted = redact_payload(payload)
    assert redacted["accessToken"] == "[REDACTED]"
    assert redacted["nested"]["authorization"] == "[REDACTED]"


def test_extracts_known_state_attributes_without_assuming_shape() -> None:
    state = {
        "response": {
            "temperature": {"currentTemperature": 23.5},
            "windStrength": "LOW",
            "display": {"light": "OFF"},
        }
    }
    assert observed_attributes(state) == {
        "currentTemperature": 23.5,
        "windStrength": "LOW",
        "light": "OFF",
    }


def test_profile_must_declare_writable_enum_value() -> None:
    profile = {
        "property": {
            "operation": {
                "airConOperationMode": {
                    "mode": ["r", "w"],
                    "value": {"w": ["POWER_OFF", "POWER_ON"]},
                }
            }
        }
    }
    assert profile_supports_writable_enum(
        profile, "operation", "airConOperationMode", "POWER_OFF"
    )
