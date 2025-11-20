"""
Configuration module using Pydantic Settings for environment variable configuration

@author: Marcin Zelek (marcin.zelek@gmail.com)
         Copyright (C) xmz. All Rights Reserved.
"""

################################################################################
# Import(s)                                                                    #
################################################################################

from typing import Literal, Optional

from pydantic import Field as _PydField
from pydantic_settings import BaseSettings, SettingsConfigDict

################################################################################
# Module                                                                       #
################################################################################


class Settings(BaseSettings):
    """Unified settings for bintexttools with environment variable support."""

    model_config = SettingsConfigDict(env_prefix="BINTEXT_", case_sensitive=False, extra="ignore")

    # Format options (for bin2text)
    format: Literal["BINARY", "DECIMAL", "HEX", "ASCII", "BASE64"] = _PydField(
        default="HEX", description="Output format for binary to text conversion"
    )
    delimiter: Optional[str] = _PydField(default=None, description="Data delimiter")
    line_characters: int = _PydField(default=0, description="Number of characters per line")
    show_header: bool = _PydField(default=True, description="Show/Add to file info header data")

    # File paths
    binary_file_path: Optional[str] = _PydField(
        default=None, description="Path to binary file (for bin2text)"
    )
    text_file_path: Optional[str] = _PydField(
        default=None, description="Path to text file (input for text2bin, output for bin2text)"
    )
    output_file_path: Optional[str] = _PydField(
        default=None, description="Output file path (for text2bin)"
    )

    # Text2Bin specific options
    header: Optional[str] = _PydField(
        default=None, description="Header JSON string for text to binary conversion"
    )
    rename_file: bool = _PydField(
        default=True, description="Ask to rename file to original (for text2bin)"
    )
    force: bool = _PydField(default=False, description="Force conversion when validation fails")

    # Logging
    logging_level: Optional[Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]] = _PydField(
        default=None, description="Logging level"
    )


################################################################################
#                                End of file                                   #
################################################################################
