import shutil
from importlib.metadata import version
from typing import Type, Tuple
from pathlib import Path
import click
from pydantic import BaseModel, DirectoryPath, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

app_name = "housaku"
app_dir = Path(click.get_app_dir(app_name=app_name))
config_file_path = app_dir / "config.toml"
template_file_path = Path(__file__).parent / "config_template.toml"


class FileSettings(BaseModel):
    include: list[DirectoryPath] = []
    exclude: list[str] = []


class FeedSettings(BaseModel):
    urls: list[str] = []


class Settings(BaseSettings):
    name: str = app_name
    description: str = (
        "A powerful personal search engine built on top of SQLite's FTS5."
    )
    version: str = version("housaku")

    sqlite_url: str = f"{app_dir / 'db.sqlite3'}"
    files: FileSettings = Field(default_factory=FileSettings)
    feeds: FeedSettings = Field(default_factory=FeedSettings)

    model_config = SettingsConfigDict(
        toml_file=config_file_path,
        extra="ignore",
    )

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

        return (
            init_settings,
            TomlConfigSettingsSource(settings_cls),
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


if __name__ == "__main__":
    settings = Settings()
    print(settings.model_dump())
