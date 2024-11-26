import os
import subprocess
import rich_click as click
from housaku.settings import config_file_path
from housaku.utils import console


@click.command(
    name="config",
    help="Opens the configuration file.",
)
def config() -> None:
    editor = os.environ.get("EDITOR", None)
    try:
        if editor:
            subprocess.run([editor, str(config_file_path)], check=True)
        else:
            subprocess.run(["open", str(config_file_path)], check=True)
    except Exception as e:
        console.print(f"[red][Err][/] Failed to open the configuration file: {e}")
