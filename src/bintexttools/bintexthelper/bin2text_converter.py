"""Binary to text converter implementation.

@author: Marcin Zelek (marcin.zelek@gmail.com)
         Copyright (C) xmz. All Rights Reserved.
"""

import binascii
import codecs
import os
import struct
from typing import Optional

from .text_format import TextFormat


class Bin2TextConverter:
    """Converts binary data to text format.

    Supports multiple output formats including binary, decimal, hexadecimal,
    ASCII, and Base64 encoding.
    """

    def __init__(
        self,
        format: TextFormat = TextFormat.HEX,
        delimiter: Optional[str] = None,
        line_characters: int = -1,
        linesep: Optional[str] = None,
    ) -> None:
        """Initialize the converter with specified parameters.

        Args:
            format: Text format to use for conversion. Defaults to HEX.
            delimiter: Optional delimiter string to insert between bytes.
            line_characters: Number of characters per line. If <= 0, no line breaks.
            linesep: Line separator string. Defaults to os.linesep.
        """
        self.linesep = linesep if linesep is not None else os.linesep
        self.format = format
        self.delimiter = delimiter
        self.line_characters = line_characters

    def _convert_byte(self, byte: bytes) -> Optional[str]:
        """Convert a single byte to text representation.

        Args:
            byte: Single byte to convert.

        Returns:
            String representation of the byte, or None if format is invalid.
        """
        if self.format == TextFormat.BINARY:
            return bin(int(binascii.hexlify(byte), 16))[2:].zfill(8)
        if self.format == TextFormat.DECIMAL:
            return str(int(binascii.hexlify(byte), 16)).zfill(3)
        if self.format == TextFormat.HEX:
            return codecs.decode(binascii.hexlify(byte), "ascii")
        if self.format == TextFormat.ASCII:
            return codecs.decode(binascii.b2a_uu(byte), "ascii").rstrip(self.linesep)
        if self.format == TextFormat.BASE64:
            return codecs.decode(binascii.b2a_base64(byte), "ascii").rstrip("==" + self.linesep)
        return None

    def convert(self, data: bytearray) -> str:
        """Convert bytearray to text string.

        Args:
            data: Bytearray to convert.

        Returns:
            Text representation of the binary data.
        """
        text = ""
        for byte in data:
            converted = self._convert_byte(struct.pack("B", byte))
            if converted:
                text += converted
        return text

    def convert_file(self, input_file: str, output_file: str, write_type: str = "w") -> None:
        """Convert binary file to text file.

        Args:
            input_file: Path to input binary file.
            output_file: Path to output text file.
            write_type: File write mode ('w' for write, 'a' for append). Defaults to 'w'.

        Raises:
            IOError: If file operations fail.
        """
        with open(input_file, "rb") as input_fp:
            with open(output_file, write_type, encoding="utf-8") as output_fp:
                first_byte = True
                line_length = 0
                while True:
                    to_write = ""
                    byte = input_fp.read(1)

                    if not byte:
                        break

                    if first_byte:
                        first_byte = False
                    elif self.delimiter:
                        to_write += self.delimiter

                    converted = self._convert_byte(byte)
                    if converted:
                        to_write += converted

                    if self.line_characters > 0:
                        count_write_characters = len(to_write)
                        if count_write_characters > 0:
                            for _ in range(count_write_characters):
                                if ((line_length + 1) % (self.line_characters + 1)) == 0:
                                    output_fp.write(self.linesep)
                                    line_length = 0
                                line_length += output_fp.write(to_write[:1])
                                to_write = to_write[1:]
                    else:
                        line_length += output_fp.write(to_write)
