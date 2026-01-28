"""Reusable validators for Medit config fields.

These validators are intended to be attached to dataclass fields via metadata:

    from dataclasses import field
    from .config_validators import validate_string

    name: str = field(default="x", metadata={"validator": validate_string(...)})

Validators should raise ValueError with a human-friendly message. The config loader
wraps that into a ConfigError that includes the config file path.
"""

from pathlib import Path
from typing import Any, Mapping, Protocol


class FieldValidator(Protocol):
    def __call__(
        self,
        value: Any,
        default: Any,
        *,
        path: Path | None,
        field_name: str,
    ) -> Any: ...


def validate_bool(*, label: str | None = None) -> FieldValidator:
    def _validator(
        value: Any,
        default: Any,
        *,
        path: Path | None,
        field_name: str,
    ) -> bool:
        if value is None:
            value = default

        display = label or field_name
        if not isinstance(value, bool):
            raise ValueError(f"{display} must be a boolean.")
        return value

    return _validator


def validate_int(
    *,
    label: str | None = None,
    min_value: int | None = None,
    max_value: int | None = None,
) -> FieldValidator:
    def _validator(
        value: Any,
        default: Any,
        *,
        path: Path | None,
        field_name: str,
    ) -> int:
        if value is None:
            value = default

        display = label or field_name
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"{display} must be an integer.")
        if min_value is not None and value < min_value:
            raise ValueError(f"{display} must be >= {min_value}.")
        if max_value is not None and value > max_value:
            raise ValueError(f"{display} must be <= {max_value}.")
        return value

    return _validator


def validate_number(
    *,
    label: str | None = None,
    min_value: float | None = None,
    max_value: float | None = None,
) -> FieldValidator:
    def _validator(
        value: Any,
        default: Any,
        *,
        path: Path | None,
        field_name: str,
    ) -> float:
        if value is None:
            value = default

        display = label or field_name
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"{display} must be a number.")

        value_f = float(value)
        if min_value is not None and value_f < min_value:
            raise ValueError(f"{display} must be >= {min_value}.")
        if max_value is not None and value_f > max_value:
            raise ValueError(f"{display} must be <= {max_value}.")
        return value_f

    return _validator


def validate_string(
    *,
    label: str | None = None,
    allow_empty: bool = True,
    forbid_newlines: bool = False,
    strip: bool = False,
    min_length: int | None = None,
    max_length: int | None = None,
) -> FieldValidator:
    def _validator(
        value: Any,
        default: Any,
        *,
        path: Path | None,
        field_name: str,
    ) -> str:
        if value is None:
            value = default

        display = label or field_name

        if not isinstance(value, str):
            raise ValueError(f"{display} must be a string.")

        if strip:
            value = value.strip()

        if not allow_empty and value == "":
            raise ValueError(f"{display} must not be empty.")
        if min_length is not None and len(value) < min_length:
            raise ValueError(f"{display} must be at least {min_length} characters.")
        if max_length is not None and len(value) > max_length:
            raise ValueError(f"{display} must be at most {max_length} characters.")
        if forbid_newlines and ("\n" in value or "\r" in value):
            raise ValueError(f"{display} must not contain newlines.")

        return value

    return _validator


def validate_one_of(*choices: Any, label: str | None = None) -> FieldValidator:
    if not choices:
        raise ValueError("validate_one_of requires at least one choice.")

    def _validator(
        value: Any,
        default: Any,
        *,
        path: Path | None,
        field_name: str,
    ) -> Any:
        if value is None:
            value = default

        display = label or field_name
        if value not in choices:
            formatted = ", ".join(repr(c) for c in choices)
            raise ValueError(f"{display} must be one of: {formatted}.")

        return value

    return _validator


def validate_list(
    *,
    label: str | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
) -> FieldValidator:
    def _validator(
        value: Any,
        default: Any,
        *,
        path: Path | None,
        field_name: str,
    ) -> list[Any]:
        if value is None:
            value = default

        display = label or field_name
        if not isinstance(value, list):
            raise ValueError(f"{display} must be a list.")
        if min_length is not None and len(value) < min_length:
            raise ValueError(f"{display} must have at least {min_length} items.")
        if max_length is not None and len(value) > max_length:
            raise ValueError(f"{display} must have at most {max_length} items.")
        return value

    return _validator


def validate_object(*, label: str | None = None) -> FieldValidator:
    def _validator(
        value: Any,
        default: Any,
        *,
        path: Path | None,
        field_name: str,
    ) -> dict[str, Any]:
        if value is None:
            value = default

        display = label or field_name
        if not isinstance(value, Mapping):
            raise ValueError(f"{display} must be an object.")
        return dict(value)

    return _validator

