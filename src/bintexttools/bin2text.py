"""BIN to ASCII converter."""

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
APPLICATION_NAME_STRING = "BIN File to TEXT File converter"


@click.command()
@click.version_option(version=VERSION_STRING, prog_name=APPLICATION_NAME_STRING)
@click.option(
    "-f",
    "--format",
    "output_format",
    type=click.Choice(["BINARY", "DECIMAL", "HEX", "ASCII", "BASE64"], case_sensitive=False),
    default="HEX",
    help="Output format.",
)
@click.option("-d", "--delimiter", default=None, help="Data delimiter")
@click.option("-l", "--line-characters", type=int, default=0, help="Number of characters per line")
@click.option(
    "--show-header/--no-show-header", default=True, help="Show/Add to file info header data"
)
@click.option(
    "-i",
    "--binary-file-path",
    type=click.Path(exists=True, readable=True),
    required=True,
    help="Path to binary file.",
)
@click.option(
    "-o",
    "--text-file-path",
    type=str,
    callback=validate_file_path,
    help="Output path to text file.",
)
@click.option(
    "-ll",
    "--logging-level",
    type=click.Choice(["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"], case_sensitive=False),
    default=None,
    help="Output log level",
)
def main(
    binary_file_path: str,
    text_file_path: Optional[str],
    output_format: str,
    delimiter: Optional[str],
    line_characters: int,
    show_header: bool,
    logging_level: Optional[str],
) -> None:
    """BIN File to TEXT File converter."""
    # Load settings from environment variables
    settings = Settings()

    # Merge CLI arguments with settings (CLI takes precedence over env vars)
    settings.binary_file_path = binary_file_path
    settings = merge_cli_with_settings(
        settings,
        text_file_path=text_file_path,
        format=output_format,
        delimiter=delimiter,
        line_characters=line_characters,
        show_header=show_header,
        logging_level=logging_level,
    )

    # Set default output filename if not provided
    if not settings.text_file_path:
        settings.text_file_path = BinTextCommon.get_timestamp_filename(True, True) + ".b2t"

    # Setup logging
    BinTextCommon.setup_logging(settings.logging_level)

    # Setup signal handler
    signal.signal(signal.SIGINT, BinTextCommon.signal_handler)

    # Log arguments
    logging.info("* Arguments:")
    args_dict = {
        "binary_file_path": settings.binary_file_path,
        "text_file_path": settings.text_file_path,
        "format": settings.format,
        "delimiter": settings.delimiter,
        "line_characters": settings.line_characters,
        "show_header": settings.show_header,
        "logging_level": settings.logging_level,
    }
    for key, value in args_dict.items():
        formatted_key = " ".join(
            "".join([w[0].upper(), w[1:].lower()])
            for w in (re.sub(r"([a-z])([A-Z])", r"\g<1> \g<2>", key)).split()
        )
        logging.info("** [%s]: [%s]", formatted_key, value)

    if not os.path.exists(settings.binary_file_path):
        raise click.ClickException(f"Binary file not found: {settings.binary_file_path}")

    click.echo(f"Converting binary file: {settings.binary_file_path}")
    click.echo(f"to text file: {settings.text_file_path}")
    click.echo("Wait...")

    if settings.logging_level == "DEBUG":
        BinText.convert_bin2text(
            settings.binary_file_path,
            settings.text_file_path,
            settings.format,
            settings.delimiter,
            settings.line_characters,
            settings.show_header,
        )
    else:
        try:
            BinText.convert_bin2text(
                settings.binary_file_path,
                settings.text_file_path,
                settings.format,
                settings.delimiter,
                settings.line_characters,
                settings.show_header,
            )
        except Exception as e:
            if settings.logging_level:
                import traceback

                traceback.print_exc()
            raise click.ClickException(str(e))

    click.echo("Done.")


if __name__ == "__main__":
    main()
