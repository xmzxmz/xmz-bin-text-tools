"""Common utility functions for binary and text conversion tools."""

import codecs
import datetime
import hashlib
import logging
import os
import string
import sys
import unicodedata
from typing import Any, Optional

import click

# Logging level choices for CLI tools
LOGGING_LEVEL_CHOICES = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}

# Valid characters for filename slugification
VALID_FILENAME_CHARS = f"-_.() {string.ascii_letters}{string.digits}"

# Default block size for file hashing
DEFAULT_BLOCKSIZE = 4096


################################################################################
# Date/Time Utilities                                                          #
################################################################################


def get_timestamp(
    include_time: bool = True,
    include_seconds: bool = False,
    include_microseconds: bool = False,
    use_utc: bool = False,
) -> str:
    """
    Generate a formatted timestamp string.

    Args:
        include_time: Include time component (hours:minutes)
        include_seconds: Include seconds in timestamp
        include_microseconds: Include microseconds in timestamp
        use_utc: Use UTC time instead of local time

    Returns:
        Formatted timestamp string (e.g., "2024-01-15 14:30" or "2024-01-15")
    """
    if use_utc:
        now = datetime.datetime.utcnow()
    else:
        now = datetime.datetime.now()

    timestamp = f"{now.year:04d}-{now.month:02d}-{now.day:02d}"

    if include_time:
        timestamp += f" {now.hour:02d}:{now.minute:02d}"
        if include_seconds:
            timestamp += f".{now.second:02d}"
            if include_microseconds:
                timestamp += f".{now.microsecond:06d}"

    return timestamp


def get_timestamp_filename(
    include_time: bool = True,
    include_seconds: bool = False,
    include_microseconds: bool = False,
    use_utc: bool = False,
) -> str:
    """
    Generate a timestamp string suitable for use in filenames.

    Args:
        include_time: Include time component (hours_minutes)
        include_seconds: Include seconds in timestamp
        include_microseconds: Include microseconds in timestamp
        use_utc: Use UTC time instead of local time

    Returns:
        Formatted timestamp string for filenames (e.g., "2024_01_15.14_30")
    """
    if use_utc:
        now = datetime.datetime.utcnow()
    else:
        now = datetime.datetime.now()

    timestamp = f"{now.year:04d}_{now.month:02d}_{now.day:02d}"

    if include_time:
        timestamp += f".{now.hour:02d}_{now.minute:02d}"
        if include_seconds:
            timestamp += f"_{now.second:02d}"
            if include_microseconds:
                timestamp += f"_{now.microsecond:06d}"

    return timestamp


################################################################################
# File Utilities                                                               #
################################################################################


def calculate_md5(filename: str, seek: int = 0, blocksize: int = DEFAULT_BLOCKSIZE) -> str:
    """
    Calculate MD5 hash of a file.

    Args:
        filename: Path to the file
        seek: Byte offset to start reading from
        blocksize: Size of blocks to read

    Returns:
        Hexadecimal MD5 hash string
    """
    hash_obj = hashlib.md5()
    with open(filename, "rb") as file:
        if seek > 0:
            file.seek(seek)
        for block in iter(lambda: file.read(blocksize), b""):
            hash_obj.update(block)
    return hash_obj.hexdigest()


def check_file_path(file_path: str) -> str:
    """
    Check that a file path can be written to.

    Args:
        file_path: Path to check

    Returns:
        The validated file path

    Raises:
        ValueError: If the file path cannot be written
    """
    if not os.access(file_path, os.W_OK):
        try:
            open(file_path, "w").close()
            os.unlink(file_path)
        except OSError:
            raise ValueError(f"{file_path} cannot be written at that location")
    return file_path


################################################################################
# String Utilities                                                             #
################################################################################


def query_yes_no(question: str, default: str = "yes") -> bool:
    """
    Prompt the user for a yes/no question.

    Args:
        question: Question to ask the user
        default: Default answer if user just presses Enter ("yes" or "no")

    Returns:
        True for yes, False for no

    Raises:
        ValueError: If default is not "yes" or "no"
    """
    valid_answers = {
        "yes": True,
        "y": True,
        "True": True,
        "T": True,
        "t": True,
        "1": True,
        "no": False,
        "n": False,
        "False": False,
        "F": False,
        "f": False,
        "0": False,
    }

    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError(f"invalid default answer: '{default}'")

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid_answers[default]
        elif choice in valid_answers:
            return valid_answers[choice]
        else:
            sys.stdout.write("Please respond with 'yes/y/t/1' or 'no/n/f/0'" + os.linesep)


def slugify(value: str) -> str:
    """
    Convert a string to a valid filename by removing invalid characters.

    Args:
        value: String to slugify

    Returns:
        Slugified string safe for use in filenames
    """
    # Normalize unicode characters and convert to ASCII
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = codecs.decode(normalized.encode("ascii", "ignore"), "ascii")

    # Filter to only valid filename characters
    return "".join(char for char in ascii_value if char in VALID_FILENAME_CHARS)


def str_to_bool(value: str) -> bool:
    """
    Convert a string representation of a boolean to a boolean value.

    Args:
        value: String to convert

    Returns:
        Boolean value

    Raises:
        TypeError: If value cannot be converted to boolean
    """
    value_lower = value.lower()
    if value_lower in ("yes", "true", "t", "y", "1"):
        return True
    elif value_lower in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise TypeError("Boolean value expected.")


################################################################################
# Logging Utilities                                                            #
################################################################################


def setup_logging(
    logging_level: Optional[str] = None,
    log_format: str = "[%(asctime)s][%(levelname)-8s] [%(module)-20s] - %(message)s",
    date_format: str = "%Y.%m.%d %H:%M.%S",
) -> None:
    """
    Configure logging based on the provided logging level.

    Args:
        logging_level: String level name (CRITICAL, ERROR, WARNING, INFO, DEBUG) or None
        log_format: Format string for log messages
        date_format: Format string for date/time in log messages
    """
    if logging_level is None:
        level = logging.CRITICAL
    else:
        level = LOGGING_LEVEL_CHOICES.get(logging_level, logging.CRITICAL)
    logging.basicConfig(format=log_format, datefmt=date_format, level=level)


def signal_handler(signum: int, frame: Any) -> None:
    """
    Signal handler for SIGINT (Ctrl+C).

    Args:
        signum: Signal number
        frame: Current stack frame
    """
    sys.exit()


################################################################################
# Click Integration                                                             #
################################################################################


def validate_file_path(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[str]:
    """
    Click callback to validate that file path can be written.

    Args:
        ctx: Click context
        param: Click parameter
        value: File path value to validate

    Returns:
        The validated file path

    Raises:
        click.BadParameter: If the file path cannot be written
    """
    if value is None:
        return value
    if not os.access(value, os.W_OK):
        try:
            open(value, "w").close()
            os.unlink(value)
        except OSError:
            raise click.BadParameter(f"{value} cannot be written at that location")
    return value


def merge_cli_with_settings(settings: Any, **cli_args: Any) -> Any:
    """
    Merge CLI arguments with settings object. CLI arguments take precedence.

    Args:
        settings: Settings object
        **cli_args: Keyword arguments from CLI

    Returns:
        Updated settings object
    """
    for key, value in cli_args.items():
        # Skip None values (not provided), but allow False, 0, empty strings
        if value is not None:
            if hasattr(settings, key):
                # Handle string values that need uppercase conversion
                if isinstance(value, str) and key in ("format", "logging_level"):
                    setattr(settings, key, value.upper())
                # For optional file paths, only set if non-empty (empty string means not provided)
                elif key in ("text_file_path", "output_file_path") and not value:
                    # Skip empty file paths - they'll use defaults
                    pass
                else:
                    setattr(settings, key, value)
    return settings


################################################################################
# Backward Compatibility Namespace                                             #
################################################################################


class BinTextCommon:
    """
    Backward compatibility namespace for legacy code.

    This class provides access to module-level functions for backward
    compatibility with existing code that uses BinTextCommon.method() syntax.
    """

    # Date/Time utilities
    get_timestamp = staticmethod(get_timestamp)
    get_timestamp_filename = staticmethod(get_timestamp_filename)

    # File utilities
    md5sum = staticmethod(calculate_md5)
    check_file_path = staticmethod(check_file_path)

    # String utilities
    query_yes_no = staticmethod(query_yes_no)
    slugify = staticmethod(slugify)
    str_to_bool = staticmethod(str_to_bool)

    # Logging utilities
    setup_logging = staticmethod(setup_logging)
    signal_handler = staticmethod(signal_handler)

    # Constants
    LOGGING_LEVEL_CHOICES = LOGGING_LEVEL_CHOICES
