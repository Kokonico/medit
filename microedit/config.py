"""Configuration loading for medit.

Config is JSON only, to keep things dependency-free on Python 3.10+.

When no config file is found, medit will try to create a default config in the
user config directory. If that fails, medit falls back to defaults and continues.
"""

import json
import os
import sys
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any, Mapping

from .config_validators import FieldValidator, validate_string


class ConfigError(Exception):
    """Raised when a config file exists but cannot be parsed/validated."""

    def __init__(self, message: str, *, path: Path | None = None):
        super().__init__(message)
        self.path = path


@dataclass(frozen=True)
class CommandsConfig:
    separator: str = field(
        default=",",
        metadata={
            "validator": validate_string(
                label="Command separator", allow_empty=False, forbid_newlines=True
            )
        },
    )


@dataclass(frozen=True)
class MeditConfig:
    commands: CommandsConfig = field(default_factory=CommandsConfig)


@dataclass(frozen=True)
class ConfigDiagnostics:
    path: Path | None = None
    warnings: tuple[str, ...] = ()
    error: str | None = None


@dataclass(frozen=True)
class ConfigResult:
    config: MeditConfig
    diagnostics: ConfigDiagnostics


_CACHED_RESULT: ConfigResult | None = None


def _user_config_dir(app_name: str) -> Path:
    match sys.platform:
        case "win32":
            base = os.getenv("APPDATA") or os.getenv("LOCALAPPDATA")
            if base:
                return Path(base) / app_name
            return Path.home() / "AppData" / "Roaming" / app_name
        case "darwin":
            return Path.home() / "Library" / "Application Support" / app_name
        case _:
            base = os.getenv("XDG_CONFIG_HOME")
            if base:
                return Path(base) / app_name
            return Path.home() / ".config" / app_name


def _expand_path(raw: str) -> Path:
    expanded = os.path.expandvars(os.path.expanduser(raw))
    return Path(expanded)


def _env_config_path() -> Path | None:
    raw = os.getenv("MEDIT_CONFIG") or os.getenv("MICROEDIT_CONFIG")
    if not raw:
        return None
    return _expand_path(raw)


def config_search_paths() -> list[Path]:
    """Return config paths in the order they should be considered."""

    paths: list[Path] = []

    # Local (project) config.
    cwd = Path.cwd()
    paths.extend(
        [
            cwd / "medit.json",
            cwd / ".medit.json",
        ]
    )

    # User config.
    user_dir = _user_config_dir("medit")
    paths.append(user_dir / "config.json")

    return paths


def default_config_path() -> Path:
    return _user_config_dir("medit") / "config.json"


def default_config_data() -> dict[str, Any]:
    return asdict(MeditConfig())


def default_config_text() -> str:
    return json.dumps(default_config_data(), indent=2, sort_keys=True) + "\n"


def write_default_config(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(default_config_text(), encoding="utf-8")


def discover_config_path() -> Path | None:
    env_path = _env_config_path()
    if env_path is not None:
        return env_path

    for path in config_search_paths():
        if path.is_file():
            return path

    return None


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ConfigError("JSON config root must be an object.", path=path)
    return data


def _load_raw_config(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix != ".json":
        raise ConfigError(
            f"Unsupported config file type '{path.suffix}'. Use .json.", path=path
        )
    return _load_json(path)


def _validate_like_default(
    value: Any, default: Any, *, path: Path | None, field_name: str
) -> Any:
    if value is None:
        return default

    match default:
        case bool():
            if isinstance(value, bool):
                return value
            raise ConfigError(f"{field_name} must be a boolean.", path=path)
        case int():
            if isinstance(value, int) and not isinstance(value, bool):
                return value
            raise ConfigError(f"{field_name} must be an integer.", path=path)
        case float():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return float(value)
            raise ConfigError(f"{field_name} must be a number.", path=path)
        case str():
            if isinstance(value, str):
                return value
            raise ConfigError(f"{field_name} must be a string.", path=path)
        case list():
            if isinstance(value, list):
                return value
            raise ConfigError(f"{field_name} must be a list.", path=path)
        case tuple():
            if isinstance(value, list):
                return tuple(value)
            if isinstance(value, tuple):
                return value
            raise ConfigError(f"{field_name} must be a list.", path=path)
        case dict():
            if isinstance(value, Mapping):
                return dict(value)
            raise ConfigError(f"{field_name} must be an object.", path=path)
        case _:
            return value


def validate_config(data: Mapping[str, Any], *, path: Path | None = None) -> ConfigResult:
    """Validate raw config data and build a typed config object."""

    warnings: list[str] = []

    if not isinstance(data, Mapping):
        raise ConfigError("Config root must be a table/object.", path=path)

    default_config = MeditConfig()
    allowed_root_keys = {f.name for f in fields(MeditConfig)}
    unknown_root_keys = sorted(set(data.keys()) - allowed_root_keys)
    if unknown_root_keys:
        warnings.append(f"Unknown top-level keys: {', '.join(unknown_root_keys)}")

    built_sections: dict[str, Any] = {}
    for section_field in fields(MeditConfig):
        section_name = section_field.name
        default_section = getattr(default_config, section_name)
        if not is_dataclass(default_section):
            raise ConfigError(
                f"Internal error: config field '{section_name}' must be a dataclass.",
                path=path,
            )

        section_data = data.get(section_name, {})
        if section_data is None:
            section_data = {}
        if not isinstance(section_data, Mapping):
            raise ConfigError(
                f"[{section_name}] must be a table/object.",
                path=path,
            )

        allowed_section_keys = {f.name for f in fields(type(default_section))}
        unknown_section_keys = sorted(set(section_data.keys()) - allowed_section_keys)
        if unknown_section_keys:
            warnings.append(
                f"Unknown [{section_name}] keys: {', '.join(unknown_section_keys)}"
            )

        section_kwargs: dict[str, Any] = {}
        for option_field in fields(type(default_section)):
            option_name = option_field.name
            field_name = f"{section_name}.{option_name}"
            default_value = getattr(default_section, option_name)
            raw_value = section_data.get(option_name, default_value)

            field_validators: tuple[FieldValidator, ...] = ()
            validators = option_field.metadata.get("validators")
            if validators is not None:
                field_validators = tuple(validators)
            else:
                validator = option_field.metadata.get("validator")
                if validator is not None:
                    field_validators = (validator,)

            if field_validators:
                value: Any = raw_value
                for validator in field_validators:
                    try:
                        value = validator(
                            value,
                            default_value,
                            path=path,
                            field_name=field_name,
                        )
                    except ConfigError:
                        raise
                    except ValueError as exc:
                        raise ConfigError(str(exc), path=path) from exc
                section_kwargs[option_name] = value
            else:
                section_kwargs[option_name] = _validate_like_default(
                    raw_value,
                    default_value,
                    path=path,
                    field_name=field_name,
                )

        built_sections[section_name] = type(default_section)(**section_kwargs)

    config = MeditConfig(**built_sections)
    return ConfigResult(
        config=config,
        diagnostics=ConfigDiagnostics(path=path, warnings=tuple(warnings)),
    )


def load_config(path: Path) -> ConfigResult:
    raw = _load_raw_config(path)
    return validate_config(raw, path=path)


def get_config_result() -> ConfigResult:
    """Load and cache the resolved config + diagnostics."""

    global _CACHED_RESULT
    if _CACHED_RESULT is not None:
        return _CACHED_RESULT

    env_path = _env_config_path()
    if env_path is not None and not env_path.is_file():
        _CACHED_RESULT = ConfigResult(
            config=MeditConfig(),
            diagnostics=ConfigDiagnostics(
                path=env_path,
                error=f"Config file from $MEDIT_CONFIG not found: {env_path}",
            ),
        )
        return _CACHED_RESULT

    config_path = discover_config_path()
    if config_path is None:
        # No config exists yet: try to create a default one in the user config dir.
        default_path = default_config_path()
        try:
            write_default_config(default_path)
            config_path = default_path
        except OSError as exc:
            _CACHED_RESULT = ConfigResult(
                config=MeditConfig(),
                diagnostics=ConfigDiagnostics(
                    path=default_path,
                    error=f"Failed to create default config: {exc}",
                ),
            )
            return _CACHED_RESULT

    try:
        _CACHED_RESULT = load_config(config_path)
        return _CACHED_RESULT
    except ConfigError as exc:
        _CACHED_RESULT = ConfigResult(
            config=MeditConfig(),
            diagnostics=ConfigDiagnostics(
                path=exc.path or config_path,
                error=str(exc),
            ),
        )
        return _CACHED_RESULT


def get_config() -> MeditConfig:
    return get_config_result().config


def clear_config_cache() -> None:
    global _CACHED_RESULT
    _CACHED_RESULT = None
