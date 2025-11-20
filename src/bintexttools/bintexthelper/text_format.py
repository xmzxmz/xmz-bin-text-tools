"""Text format enumeration for binary-to-text conversion.

@author: Marcin Zelek (marcin.zelek@gmail.com)
         Copyright (C) xmz. All Rights Reserved.
"""

from enum import Enum


class TextFormat(Enum):
    """Enumeration of supported text formats for binary conversion."""

    BINARY = 1
    """Binary format (8-bit binary representation)."""

    DECIMAL = 2
    """Decimal format (3-digit decimal representation)."""

    HEX = 3
    """Hexadecimal format (2-character hex representation)."""

    ASCII = 4
    """ASCII/UU-encoded format."""

    BASE64 = 5
    """Base64 encoded format."""
