"""Text to binary converter implementation.

@author: Marcin Zelek (marcin.zelek@gmail.com)
         Copyright (C) xmz. All Rights Reserved.
"""

import binascii
import os
import sys
from typing import Any, Dict, Optional

from bintexttools import BinTextCommon

from .text_format import TextFormat

# Constants
START_HEADER_TAG = "<<< HEADER"
END_HEADER_TAG = ">>> HEADER"
DEFAULT_READ_BLOCK_SIZE = 4096


class Text2BinConverter:
    """Converts text data back to binary format.

    Supports multiple input formats including binary, decimal, hexadecimal,
    ASCII, and Base64 encoding. Can detect and parse header information
    from converted files.
    """

    def __init__(
        self,
        format: TextFormat = TextFormat.HEX,
        delimiter: Optional[str] = None,
        byteorder: Optional[str] = None,
        linesep: Optional[str] = None,
    ) -> None:
        """Initialize the converter with specified parameters.

        Args:
            format: Text format to use for conversion. Defaults to HEX.
            delimiter: Optional delimiter string used in text data.
            byteorder: Byte order for conversion ('little' or 'big'). Defaults to sys.byteorder.
            linesep: Line separator string. Defaults to os.linesep.
        """
        self.byteorder = byteorder if byteorder is not None else sys.byteorder
        self.linesep = linesep if linesep is not None else os.linesep
        self.format = format
        self.delimiter = delimiter
        self.filesize: Optional[int] = None
        self.md5: Optional[str] = None

    @property
    def start_header_tag(self) -> str:
        """Get the start header tag string."""
        return START_HEADER_TAG

    @property
    def end_header_tag(self) -> str:
        """Get the end header tag string."""
        return END_HEADER_TAG

    def _read_size(self) -> int:
        """Get the byte size for the current format.

        Returns:
            Number of characters needed to represent one byte in the current format.
        """
        size_map = {
            TextFormat.BINARY: 8,
            TextFormat.DECIMAL: 3,
            TextFormat.HEX: 2,
            TextFormat.ASCII: 5,
            TextFormat.BASE64: 2,
        }
        return size_map[self.format]

    def _convert_byte(self, byte_text: str) -> Optional[bytes]:
        """Convert text representation of a byte back to binary.

        Args:
            byte_text: Text representation of a byte.

        Returns:
            Binary byte data, or None if conversion fails.
        """
        try:
            if self.format == TextFormat.BINARY:
                return int(byte_text, 2).to_bytes(1, byteorder=self.byteorder)
            if self.format == TextFormat.DECIMAL:
                return int(byte_text, 10).to_bytes(1, byteorder=self.byteorder)
            if self.format == TextFormat.HEX:
                return binascii.unhexlify(byte_text)
            if self.format == TextFormat.ASCII:
                return binascii.a2b_uu(f"{byte_text}{self.linesep}")
            if self.format == TextFormat.BASE64:
                return binascii.a2b_base64(f"{byte_text}=={self.linesep}")
        except (binascii.Error, ValueError):
            pass
        return None

    def convert(self, text_data: str) -> Optional[bytes]:
        """Convert text string to binary data.

        Args:
            text_data: Text representation of binary data.

        Returns:
            Binary data as bytes, or None if conversion fails.
        """
        data: Optional[bytes] = None
        byte_size = self._read_size()
        remaining_text = text_data

        while True:
            try:
                if byte_size <= len(remaining_text):
                    byte_text = remaining_text[:byte_size]
                    remaining_text = remaining_text[byte_size:]
                    byte = self._convert_byte(byte_text)
                    if byte:
                        if data:
                            data += byte
                        else:
                            data = byte
                    else:
                        break
                else:
                    break
            except (TypeError, EOFError):
                break
        return data

    def detect_header(self, input_file: str) -> Optional[str]:
        """Detect and extract header from input file.

        Args:
            input_file: Path to input text file.

        Returns:
            Header string if found, None otherwise.

        Raises:
            IOError: If file cannot be read.
        """
        header = ""
        try:
            with open(input_file, "r", encoding="utf-8") as file_fp:
                start = end = False
                for line in file_fp:
                    if line.strip().startswith(START_HEADER_TAG):
                        start = True
                    elif line.strip().startswith(END_HEADER_TAG):
                        end = True
                        break
                    elif start:
                        header += line
                if not (start and end):
                    header = None
        except IOError:
            raise
        return header

    def detect_data_seek(self, input_file: str) -> int:
        """Detect the byte offset where data starts in the file.

        Args:
            input_file: Path to input text file.

        Returns:
            Byte offset where data starts (after header if present).

        Raises:
            IOError: If file cannot be read.
        """
        filesize = 0
        try:
            filestat = os.stat(input_file)
            filesize = filestat.st_size
        except OSError:
            filesize = 0

        seek = 0
        try:
            with open(input_file, "rb") as file_fp:
                start = end = False
                header_size = 0
                while True:
                    line = file_fp.readline()
                    if not line:
                        break
                    try:
                        line_str = line.decode("ascii")
                        header_size += len(line_str)
                        if line_str.strip().startswith(START_HEADER_TAG):
                            start = True
                        elif line_str.strip().startswith(END_HEADER_TAG):
                            end = True
                            break
                    except UnicodeDecodeError:
                        break
                if start and end:
                    seek = file_fp.tell()
                    if 0 < filesize < seek:
                        if 0 < header_size < filesize:
                            seek = header_size
                        else:
                            seek = 0
        except IOError:
            raise
        return seek

    def verify_input_file(
        self, input_file: str, seek: int, filesize: int, md5: str
    ) -> Dict[str, Any]:
        """Verify input file matches expected size and MD5 hash.

        Args:
            input_file: Path to input file.
            seek: Byte offset where data starts.
            filesize: Expected file size.
            md5: Expected MD5 hash.

        Returns:
            Dictionary with verification status and details.
        """
        size_input_data: Optional[int] = None
        md5_input_data: Optional[str] = None

        try:
            filestat = os.stat(input_file)
            size_input_data = filestat.st_size - seek
            md5_input_data = BinTextCommon.md5sum(input_file, seek)
        except (OSError, IOError):
            size_input_data = None
            md5_input_data = None

        status: Dict[str, Any] = {
            "verified": size_input_data == filesize and md5_input_data == md5,
            "expected": {"size": filesize, "md5": md5},
            "obtained": {"size": size_input_data, "md5": md5_input_data},
        }
        return status

    def verify_output_file(self, output_file: str, filesize: int, md5: str) -> Dict[str, Any]:
        """Verify output file matches expected size and MD5 hash.

        Args:
            output_file: Path to output file.
            filesize: Expected file size.
            md5: Expected MD5 hash.

        Returns:
            Dictionary with verification status and details.
        """
        size_output_file: Optional[int] = None
        md5_output_file: Optional[str] = None

        try:
            filestat = os.stat(output_file)
            size_output_file = filestat.st_size
            md5_output_file = BinTextCommon.md5sum(output_file)
        except (OSError, IOError):
            size_output_file = None
            md5_output_file = None

        status: Dict[str, Any] = {
            "verified": size_output_file == filesize and md5_output_file == md5,
            "expected": {"size": filesize, "md5": md5},
            "obtained": {"size": size_output_file, "md5": md5_output_file},
        }
        return status

    def convert_file(
        self,
        input_file: str,
        output_file: str,
        input_file_seek: int = 0,
        read_block_size: int = DEFAULT_READ_BLOCK_SIZE,
    ) -> None:
        """Convert text file to binary file.

        Args:
            input_file: Path to input text file.
            output_file: Path to output binary file.
            input_file_seek: Byte offset where data starts in input file.
            read_block_size: Size of blocks to read from input file.

        Raises:
            IOError: If file operations fail.
        """
        with open(input_file, "r", encoding="utf-8") as input_fp:
            if input_file_seek > 0:
                input_fp.seek(input_file_seek)
            with open(output_file, "wb") as output_fp:
                block_data = ""
                byte_size = self._read_size()

                while True:
                    try:
                        if byte_size > len(block_data):
                            # Read new data block
                            new_data = input_fp.read(read_block_size)
                            if not new_data:
                                break
                            block_data += new_data
                            # Remove line separators but preserve other whitespace
                            block_data = block_data.replace(self.linesep, "")

                        if byte_size <= len(block_data):
                            byte_text = block_data[:byte_size]
                            block_data = block_data[byte_size:]

                            to_write = self._convert_byte(byte_text)
                            if to_write:
                                output_fp.write(to_write)
                            else:
                                break
                        else:
                            break

                        # Detect delimiter
                        if self.delimiter:
                            if len(self.delimiter) > len(block_data):
                                # Read new data block
                                new_data = input_fp.read(read_block_size)
                                if not new_data:
                                    break
                                block_data += new_data
                                block_data = block_data.replace(self.linesep, "")

                            if len(self.delimiter) <= len(block_data):
                                delimiter = block_data[: len(self.delimiter)]
                                block_data = block_data[len(self.delimiter) :]

                                if delimiter != self.delimiter:
                                    break
                            else:
                                break

                    except (TypeError, EOFError, IOError):
                        break
