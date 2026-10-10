"""Read the deliberately simple .env file without a third-party dependency."""

import os
from pathlib import Path


class ConfigError(ValueError):
    pass


def read_env(path=None):
    path = Path(path or os.environ.get("TEST1024_ENV", ".env"))
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc
    values = {}
    for number, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ConfigError(f"{path}:{number}: expected KEY=value")
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def server_config(path=None):
    values = read_env(path)
    required = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")
    missing = [key for key in required if not values.get(key)]
    if missing:
        raise ConfigError("fill in .env: " + ", ".join(missing))
    try:
        db_port = int(values["DB_PORT"])
        app_port = int(values.get("APP_PORT", "8024"))
    except ValueError as exc:
        raise ConfigError("DB_PORT and APP_PORT must be numbers") from exc
    if not 1 <= db_port <= 65535 or not 1 <= app_port <= 65535:
        raise ConfigError("ports must be between 1 and 65535")
    if values.get("APP_HOST", "127.0.0.1") != "127.0.0.1":
        raise ConfigError("APP_HOST must be 127.0.0.1")
    return {
        "db_host": values["DB_HOST"],
        "db_port": db_port,
        "db_name": values["DB_NAME"],
        "db_user": values["DB_USER"],
        "db_password": values["DB_PASSWORD"],
        "app_port": app_port,
    }


def client_port(path=None):
    # The installed command works from any directory with the default port.
    # An explicit config path supports deployments that change APP_PORT.
    if path is None and not os.environ.get("TEST1024_ENV") and not Path(".env").exists():
        return 8024
    values = read_env(path)
    try:
        port = int(values.get("APP_PORT", "8024"))
    except ValueError as exc:
        raise ConfigError("APP_PORT must be a number") from exc
    if not 1 <= port <= 65535:
        raise ConfigError("APP_PORT must be between 1 and 65535")
    return port
