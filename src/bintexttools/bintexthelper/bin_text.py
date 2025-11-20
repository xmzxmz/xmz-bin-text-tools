"""Main binary-to-text and text-to-binary conversion interface.

@author: Marcin Zelek (marcin.zelek@gmail.com)
         Copyright (C) xmz. All Rights Reserved.
"""

import json
import logging
import ntpath
import os
import sys
import tempfile
from typing import Any, Dict, Optional

from bintexttools import BinTextCommon

from .bin2text_converter import Bin2TextConverter
from .text2bin_converter import END_HEADER_TAG, START_HEADER_TAG, Text2BinConverter
from .text_format import TextFormat

# Constants
VERSION = 1
BUFFER_SIZE = 1024


class BinText:
    """Main interface for binary-to-text and text-to-binary conversion.

    Provides high-level methods for converting between binary and text formats
    with support for headers, validation, and file management.
    """

    version = VERSION

    @staticmethod
    def convert_bin2text(
        binary_file_path: str,
        text_file_path: str,
        format: str,
        delimiter: Optional[str],
        line_characters: int,
        show_header: bool,
    ) -> None:
        """Convert binary file to text file.

        Args:
            binary_file_path: Path to input binary file.
            text_file_path: Path to output text file.
            format: Text format (BINARY, DECIMAL, HEX, ASCII, BASE64).
            delimiter: Optional delimiter string between bytes.
            line_characters: Number of characters per line (0 for no line breaks).
            show_header: If True, include header in output file; if False, print to console.

        Raises:
            OSError: If file operations fail.
            ValueError: If format is invalid.
        """
        logging.info("Convert BIN data to TEXT Data ...")

        input_file = binary_file_path
        output_file_with_header = output_file = text_file_path

        try:
            filestat = os.stat(input_file)
        except OSError as e:
            raise OSError(f"Cannot access input file: {input_file}") from e

        header_data: Dict[str, Any] = {"version": BinText.version}
        header_data["binFile"] = {
            "timestamp": BinTextCommon.get_timestamp(),
            "filename": ntpath.basename(input_file),
            "filesize": filestat.st_size,
            "md5": BinTextCommon.md5sum(input_file),
        }

        if show_header:
            output_file = tempfile.NamedTemporaryFile(delete=True).name

        try:
            text_format = TextFormat[format]
        except KeyError:
            raise ValueError(f"Invalid format: {format}") from None

        bin2text = Bin2TextConverter(
            format=text_format,
            delimiter=delimiter,
            line_characters=line_characters,
        )
        bin2text.convert_file(input_file, output_file)

        try:
            filestat = os.stat(output_file)
        except OSError as e:
            raise OSError(f"Cannot access output file: {output_file}") from e

        header_data["textFile"] = {
            "filesize": filestat.st_size,
            "md5Data": BinTextCommon.md5sum(output_file),
            "format": format,
            "delimiter": delimiter,
            "lineCharacters": line_characters,
            "linesep": os.linesep,
            "byteorder": sys.byteorder,
        }

        if show_header:
            with open(output_file_with_header, "w", encoding="utf-8") as output_fp:
                output_fp.write(START_HEADER_TAG + os.linesep)
                header_string = json.dumps(header_data, indent=4) + os.linesep
                logging.info(header_string)
                output_fp.write(header_string)
                output_fp.write(END_HEADER_TAG + os.linesep)
                with open(output_file, "r", encoding="utf-8") as input_fp:
                    while True:
                        data = input_fp.read(BUFFER_SIZE)
                        if not data:
                            break
                        output_fp.write(data)
                os.remove(output_file)
        else:
            header_string = json.dumps(header_data, indent=4) + os.linesep
            print(os.linesep)
            print(
                "********************************************************************************"
            )
            print("* Header - save it and use to decode data")
            print(
                "********************************************************************************"
            )
            print(header_string)
            print(
                "********************************************************************************"
            )
            print(os.linesep)

    @staticmethod
    def _get_header_for_convert_text2bin(header: Optional[str]) -> Optional[Dict[str, Any]]:
        """Parse header JSON string.

        Args:
            header: JSON string containing header data.

        Returns:
            Parsed header dictionary, or None if parsing fails.
        """
        if not header:
            return None
        try:
            header_data = json.loads(header)
            return header_data
        except json.JSONDecodeError as error:
            logging.error(f"Error decoding header data: {error}")
            return None

    @staticmethod
    def _use_header_for_convert_text2bin(
        header: Optional[str], text2bin: Text2BinConverter
    ) -> Text2BinConverter:
        """Apply header settings to text2bin converter.

        Args:
            header: JSON string containing header data.
            text2bin: Text2BinConverter instance to configure.

        Returns:
            Configured Text2BinConverter instance.
        """
        header_data = BinText._get_header_for_convert_text2bin(header)
        if header_data and "textFile" in header_data:
            text_file_info = header_data["textFile"]
            if "byteorder" in text_file_info:
                text2bin.byteorder = text_file_info["byteorder"]
            if "linesep" in text_file_info:
                text2bin.linesep = text_file_info["linesep"]
            if "format" in text_file_info:
                try:
                    text2bin.format = TextFormat[text_file_info["format"]]
                except KeyError:
                    logging.warning(f"Invalid format in header: {text_file_info['format']}")
            if "delimiter" in text_file_info:
                text2bin.delimiter = text_file_info["delimiter"]
        return text2bin

    @staticmethod
    def convert_text2bin(
        text_file_path: str,
        output_file_path: str,
        header: Optional[str] = None,
        rename_file: bool = False,
        default_output_filename: Optional[str] = None,
        force: bool = False,
    ) -> None:
        """Convert text file to binary file.

        Args:
            text_file_path: Path to input text file.
            output_file_path: Path to output binary file.
            header: Optional JSON header string with format information.
            rename_file: If True, prompt to rename file to original name from header.
            default_output_filename: Default output filename for rename logic.

        Raises:
            OSError: If file operations fail.
            ValueError: If header data is invalid.
        """
        logging.info("Convert TEXT data to BIN Data ...")

        input_file = text_file_path
        output_file = output_file_path
        text2bin = Text2BinConverter()
        text2bin = BinText._use_header_for_convert_text2bin(header, text2bin)
        input_file_seek = text2bin.detect_data_seek(input_file)
        detected_header = text2bin.detect_header(input_file)
        if detected_header:
            header = detected_header

        header_data: Optional[Dict[str, Any]] = None
        if header:
            header_data = BinText._get_header_for_convert_text2bin(header)
            if header_data and "textFile" in header_data:
                if not detected_header:
                    logging.debug("HeaderData: " + json.dumps(header_data, indent=4))
                text2bin = BinText._use_header_for_convert_text2bin(header, text2bin)
                if all(key in header_data["textFile"] for key in ["filesize", "md5Data"]):
                    status = text2bin.verify_input_file(
                        input_file,
                        input_file_seek,
                        header_data["textFile"]["filesize"],
                        header_data["textFile"]["md5Data"],
                    )
                    if status.get("verified"):
                        print("The text file is correct.")
                        logging.debug(json.dumps(status, indent=4) + os.linesep)
                    else:
                        print("The text file is corrupted.")
                        print(json.dumps(status, indent=4) + os.linesep)
                        if not force:
                            raise ValueError(
                                "Input text file failed validation. "
                                "Use --force to continue conversion."
                            )
                        print("Trying to convert invalid text data ...")

        output_file_name = ntpath.basename(output_file)
        output_file_dir = ntpath.dirname(output_file)
        text2bin.convert_file(input_file, output_file, input_file_seek)

        if header_data and "binFile" in header_data:
            if all(key in header_data["binFile"] for key in ["filesize", "md5"]):
                status = text2bin.verify_output_file(
                    output_file,
                    header_data["binFile"]["filesize"],
                    header_data["binFile"]["md5"],
                )
                if "verified" in status:
                    if status["verified"]:
                        print("The output file is correct.")
                        logging.debug(json.dumps(status, indent=4) + os.linesep)
                        if (
                            rename_file
                            and "filename" in header_data["binFile"]
                            and header_data["binFile"]["filename"] != output_file_name
                        ):
                            output_file_location = os.path.join(
                                output_file_dir,
                                BinTextCommon.slugify(header_data["binFile"]["filename"]),
                            )
                            print(
                                f"Updating output file into original to location: "
                                f"{output_file_location}"
                            )
                            if os.path.exists(output_file_location):
                                print(
                                    f"The file '{output_file_location}' already exists. "
                                    f"Skipped ..."
                                )
                            else:
                                os.rename(output_file, output_file_location)
                    else:
                        print("The output file is corrupted.")
                        print(json.dumps(status, indent=4) + os.linesep)
