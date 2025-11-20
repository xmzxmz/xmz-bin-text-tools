"""
Tools for binary and text data

@author: Marcin Zelek (marcin.zelek@gmail.com)
         Copyright (C) xmz. All Rights Reserved.
"""

################################################################################
# Import(s)                                                                    #
################################################################################

import json
from typing import Dict, Optional

from .bintextcommon import BinTextCommon
from .bintexthelper import Bin2TextConverter, BinText, Text2BinConverter, TextFormat

################################################################################
# Module                                                                       #
################################################################################


def bin2text(
    binary_file_path: str,
    text_file_path: str,
    format: str = "HEX",
    delimiter: Optional[str] = None,
    line_characters: int = 0,
    show_header: bool = True,
) -> None:
    BinText.convert_bin2text(
        binary_file_path, text_file_path, format, delimiter, line_characters, show_header
    )


def text2bin(
    text_file_path: str,
    binary_file_path: str,
    format: str = "HEX",
    delimiter: Optional[str] = None,
    *,
    header: Optional[str] = None,
    rename_file: bool = False,
    force: bool = False,
) -> None:
    resolved_header = header
    if resolved_header is None:
        header_payload: Dict[str, Dict[str, object]] = {"textFile": {}}
        if format:
            header_payload["textFile"]["format"] = format.upper()
        if delimiter is not None:
            header_payload["textFile"]["delimiter"] = delimiter

        if header_payload["textFile"]:
            resolved_header = json.dumps(header_payload)

    BinText.convert_text2bin(
        text_file_path=text_file_path,
        output_file_path=binary_file_path,
        header=resolved_header,
        rename_file=rename_file,
        default_output_filename=None,
        force=force,
    )


__all__ = ("BinTextCommon", "Bin2TextConverter", "BinText", "TextFormat", "Text2BinConverter")

################################################################################
#                                End of file                                   #
################################################################################
