"""TEXT File to BIN File converter."""

import json
import logging
import os
import re
import signal
from typing import Optional

import click

from bintexttools.bintextcommon import (
    BinTextCommon,
    Settings,
    merge_cli_with_settings,
    validate_file_path,
)
from bintexttools.bintexthelper import BinText

VERSION_STRING = "0.2.0"
APPLICATION_NAME_STRING = "TEXT File to BIN File converter"


@click.command()
@click.version_option(version=VERSION_STRING, prog_name=APPLICATION_NAME_STRING)
@click.option("--header", default=None, help="The header to decode data (JSON format).")
@click.option(
    "--rename-file/--no-rename-file",
    default=True,
    help="Automatically rename output file to original when metadata is available.",
)
@click.option(
    "--skip-rename",
    is_flag=True,
    default=False,
    help="Skip renaming output file even if metadata contains original filename.",
)
@click.option(
    "-i",
    "--text-file-path",
    type=click.Path(exists=True, readable=True),
    required=True,
    help="Path to file with text data.",
)
@click.option(
    "-o",
    "--output-file-path",
    type=str,
    callback=validate_file_path,
    help="Output path.",
)
@click.option(
    "-ll",
    "--logging-level",
    type=click.Choice(["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"], case_sensitive=False),
    default=None,
    help="Output log level",
)
@click.option(
    "--force/--no-force",
    default=False,
    help="Force conversion even if validation of text data fails.",
)
def main(
    text_file_path: str,
    output_file_path: Optional[str],
    header: Optional[str],
    rename_file: bool,
    skip_rename: bool,
    logging_level: Optional[str],
    force: bool,
) -> None:
    """TEXT File to BIN File converter."""
    # Load settings from environment variables
    settings = Settings()

    # Default header if not provided
    default_header = json.dumps(
        {
            "textFile": {
                "format": "HEX",
                "linesep": "\n",
                "byteorder": "little",
                "delimiter": None,
                "lineCharacters": 0,
            }
        }
    )
    default_output_filename = BinTextCommon.get_timestamp_filename(True, True) + ".t2b"

    # Merge CLI arguments with settings (CLI takes precedence over env vars)
    settings.text_file_path = text_file_path
    settings = merge_cli_with_settings(
        settings,
        output_file_path=output_file_path,
        header=header,
        rename_file=rename_file,
        logging_level=logging_level,
        force=force,
    )

    if skip_rename:
        settings.rename_file = False

    # Set default header if not provided
    if not settings.header:
        settings.header = default_header

    # Set default output filename if not provided
    if not settings.output_file_path:
        settings.output_file_path = default_output_filename

    # If output file path is not the default, disable rename_file
    if settings.output_file_path != default_output_filename:
        settings.rename_file = False

    # Setup logging
    BinTextCommon.setup_logging(settings.logging_level)

    # Setup signal handler
    signal.signal(signal.SIGINT, BinTextCommon.signal_handler)

    # Log arguments
    logging.info("* Arguments:")
    args_dict = {
        "text_file_path": settings.text_file_path,
        "output_file_path": settings.output_file_path,
        "header": settings.header,
        "rename_file": settings.rename_file,
        "logging_level": settings.logging_level,
        "force": settings.force,
    }
    for key, value in args_dict.items():
        formatted_key = " ".join(
            "".join([w[0].upper(), w[1:].lower()])
            for w in (re.sub(r"([a-z])([A-Z])", r"\g<1> \g<2>", key)).split()
        )
        logging.info("** [%s]: [%s]", formatted_key, value)

    if not os.path.exists(settings.text_file_path):
        raise click.ClickException(f"Text file not found: {settings.text_file_path}")

    click.echo(f"Converting text file: {settings.text_file_path}")
    click.echo(f"to original file: {settings.output_file_path}")
    click.echo("Wait...")

    conversion_kwargs = dict(
        text_file_path=settings.text_file_path,
        output_file_path=settings.output_file_path,
        header=settings.header,
        rename_file=settings.rename_file,
        default_output_filename=default_output_filename,
        force=settings.force,
    )
    if settings.logging_level == "DEBUG":
        BinText.convert_text2bin(**conversion_kwargs)
    else:
        try:
            BinText.convert_text2bin(**conversion_kwargs)
        except Exception as e:
            if settings.logging_level:
                import traceback

                traceback.print_exc()
            raise click.ClickException(str(e))

    click.echo("Done.")


if __name__ == "__main__":
    main()
