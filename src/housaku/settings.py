from typing import Type, Tuple
from pathlib import Path
import shutil
import click
from pydantic import BaseModel, DirectoryPath
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

app_dir = Path(click.get_app_dir(app_name="housaku"))
config_file_path = app_dir / "config.toml"
template_file_path = Path(__file__).parent / "config_template.toml"


class Files(BaseModel):
    include: list[DirectoryPath] = []
    exclude: list[str] = []


class Feeds(BaseModel):
    urls: list[str] = []


class Settings(BaseSettings):
    sqlite_url: str = f"{app_dir / 'db.sqlite3'}"
    files: Files = Files()
    feeds: Feeds = Feeds()

    model_config = SettingsConfigDict(toml_file=config_file_path)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        app_dir.mkdir(parents=True, exist_ok=True)

        if not config_file_path.exists():
            shutil.copy(template_file_path, config_file_path)

        return (TomlConfigSettingsSource(settings_cls),)
