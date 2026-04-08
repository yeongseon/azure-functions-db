from __future__ import annotations

from dataclasses import dataclass
import os
import re

from .errors import ConfigurationError

_ENV_VAR_PATTERN = re.compile(r"^%(\w+)%$")


def resolve_env_vars(value: str) -> str:
    match = _ENV_VAR_PATTERN.match(value)
    if match is None:
        return value

    var_name = match.group(1)
    resolved = os.environ.get(var_name)
    if resolved is None:
        msg = f"Environment variable '{var_name}' is not set"
        raise ConfigurationError(msg)
    return resolved


@dataclass(frozen=True, slots=True, kw_only=True)
class DbConfig:
    connection_url: str
    pool_size: int = 5
    pool_recycle: int = 3600
    echo: bool = False
    connect_args: dict[str, object] | None = None
