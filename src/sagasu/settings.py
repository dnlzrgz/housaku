from typing import Type, Tuple
from pathlib import Path
import click
from pydantic import DirectoryPath
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

_app_dir = Path(click.get_app_dir(app_name="sagasu"))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(toml_file=f"{_app_dir / 'config.toml'}")

    sqlite_url: str = f"sqlite:///{_app_dir / 'db.sqlite3'}"
    directories: dict[str, DirectoryPath] = {}

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        _app_dir.mkdir(parents=True, exist_ok=True)
        return (TomlConfigSettingsSource(settings_cls),)
