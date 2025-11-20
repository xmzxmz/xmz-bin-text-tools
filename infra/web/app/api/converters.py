"""Converter API endpoints."""

import base64
import json
import logging
import ntpath
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Optional
from unittest.mock import patch

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from bintexttools.bintextcommon import BinTextCommon
from bintexttools.bintexthelper import BinText
from bintexttools.bintexthelper.text2bin_converter import END_HEADER_TAG, START_HEADER_TAG

logger = logging.getLogger(__name__)

router = APIRouter()

# Templates
_templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))


@contextmanager
def non_interactive_mode():
    """Context manager to disable interactive prompts for web API."""
    # Mock query_yes_no to always return True to avoid blocking
    with patch.object(BinTextCommon, "query_yes_no", return_value=True):
        yield


def update_header_with_original_filename(file_path: str, original_filename: str) -> None:
    """Update the header in the output file to include the original filename."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check if header exists
        if START_HEADER_TAG not in content or END_HEADER_TAG not in content:
            return

        # Extract header section
        start_idx = content.find(START_HEADER_TAG)
        end_tag_idx = content.find(END_HEADER_TAG)

        if start_idx == -1 or end_tag_idx == -1:
            return

        end_idx = end_tag_idx + len(END_HEADER_TAG)
        header_section = content[start_idx:end_idx]
        rest_of_content = content[end_idx:]

        # Find the JSON part between tags
        json_start = header_section.find("\n", header_section.find(START_HEADER_TAG)) + 1
        json_end = header_section.rfind("\n", 0, header_section.find(END_HEADER_TAG))
        json_str = header_section[json_start:json_end].strip()

        try:
            header_data = json.loads(json_str)
            # Update the filename in binFile
            if "binFile" in header_data and isinstance(header_data["binFile"], dict):
                header_data["binFile"]["filename"] = original_filename

            # Reconstruct the file with updated header
            new_header_section = (
                START_HEADER_TAG
                + os.linesep
                + json.dumps(header_data, indent=4)
                + os.linesep
                + END_HEADER_TAG
                + os.linesep
            )

            new_content = content[:start_idx] + new_header_section + rest_of_content

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
        except json.JSONDecodeError:
            # If header is malformed, skip update
            pass
    except Exception as e:
        logger.warning(f"Failed to update header with original filename: {e}")


def extract_filename_from_header(header: Optional[str]) -> Optional[str]:
    """Extract the original filename from the header JSON."""
    if not header:
        return None
    try:
        header_data = json.loads(header)
        if isinstance(header_data, dict) and "binFile" in header_data:
            if isinstance(header_data["binFile"], dict) and "filename" in header_data["binFile"]:
                return header_data["binFile"]["filename"]
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    return None


def extract_filename_from_text_file(file_path: str) -> Optional[str]:
    """Extract the original filename from the header in a text file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if START_HEADER_TAG not in content or END_HEADER_TAG not in content:
            return None

        # Extract header section
        start_idx = content.find(START_HEADER_TAG)
        end_idx = content.find(END_HEADER_TAG)

        if start_idx == -1 or end_idx == -1:
            return None

        # Find the JSON part between tags
        json_start = content.find("\n", start_idx) + 1
        json_str = content[json_start:end_idx].strip()

        try:
            header_data = json.loads(json_str)
            if "binFile" in header_data and isinstance(header_data["binFile"], dict):
                if "filename" in header_data["binFile"]:
                    return header_data["binFile"]["filename"]
        except json.JSONDecodeError:
            pass
    except Exception:
        pass
    return None


# Pydantic models for text input endpoints
class Bin2TextTextRequest(BaseModel):
    """Request model for bin2text with text input."""

    data: str  # Base64-encoded binary data
    format: str = "HEX"
    delimiter: Optional[str] = None
    line_characters: int = 0
    show_header: bool = True


class Text2BinTextRequest(BaseModel):
    """Request model for text2bin with text input."""

    text: str  # Text content to convert
    header: Optional[str] = None
    rename_file: bool = False


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main page with Bootstrap 5 UI."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request},
    )


@router.post("/api/bin2text")
async def convert_bin2text(
    file: UploadFile = File(..., description="Binary file to convert"),
    format: str = Form(
        default="HEX", description="Output format: BINARY, DECIMAL, HEX, ASCII, BASE64"
    ),
    delimiter: Optional[str] = Form(default=None, description="Optional delimiter between bytes"),
    line_characters: int = Form(
        default=0, description="Number of characters per line (0 for no line breaks)"
    ),
    show_header: bool = Form(default=True, description="Include header in output"),
):
    """Convert binary file to text format."""
    if format.upper() not in ["BINARY", "DECIMAL", "HEX", "ASCII", "BASE64"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format: {format}. Must be one of: BINARY, DECIMAL, HEX, ASCII, BASE64",
        )

    # Create temporary files
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as input_file:
        input_path = input_file.name
        try:
            # Write uploaded file to temp file
            content = await file.read()
            input_file.write(content)
            input_file.flush()

            # Create output temp file
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".txt", encoding="utf-8"
            ) as output_file:
                output_path = output_file.name

            try:
                # Perform conversion
                BinText.convert_bin2text(
                    binary_file_path=input_path,
                    text_file_path=output_path,
                    format=format.upper(),
                    delimiter=delimiter,
                    line_characters=line_characters,
                    show_header=show_header,
                )

                # Update header with original filename if header is shown
                original_name = file.filename or "input.bin"
                if show_header:
                    update_header_with_original_filename(output_path, original_name)

                # Read output file
                with open(output_path, "rb") as f:
                    output_content = f.read()

                # Determine filename
                base_name = os.path.splitext(original_name)[0]
                output_filename = f"{base_name}.{format.lower()}.txt"

                return StreamingResponse(
                    iter([output_content]),
                    media_type="text/plain",
                    headers={"Content-Disposition": f'attachment; filename="{output_filename}"'},
                )
            finally:
                # Cleanup
                if os.path.exists(output_path):
                    os.unlink(output_path)
        finally:
            # Cleanup
            if os.path.exists(input_path):
                os.unlink(input_path)


@router.post("/api/text2bin")
async def convert_text2bin(
    file: UploadFile = File(..., description="Text file to convert"),
    header: Optional[str] = Form(
        default=None,
        description=(
            "JSON header with format information " "(optional, auto-detected if present in file)"
        ),
    ),
    rename_file: bool = Form(default=False, description="Rename file to original name from header"),
):
    """Convert text file to binary format."""
    # For web API, we disable rename_file to avoid interactive prompts
    # We'll handle filename in response headers instead
    actual_rename_file = False

    # Create temporary files
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".txt", encoding="utf-8"
    ) as input_file:
        input_path = input_file.name
        try:
            # Write uploaded file to temp file
            content = await file.read()
            input_file.write(content.decode("utf-8"))
            input_file.flush()

            # Create output temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as output_file:
                output_path = output_file.name

            try:
                # Perform conversion (with rename_file=False to avoid interactive prompts)
                # Use non_interactive_mode to mock query_yes_no for validation prompts
                with non_interactive_mode():
                    BinText.convert_text2bin(
                        text_file_path=input_path,
                        output_file_path=output_path,
                        header=header,
                        rename_file=actual_rename_file,
                        default_output_filename=None,
                        force=True,
                    )

                # Check if file exists at original path (it might have been renamed)
                final_output_path = output_path
                if not os.path.exists(output_path):
                    # File might have been renamed - try to find it
                    output_file_dir = ntpath.dirname(output_path)
                    if header:
                        try:
                            header_data = json.loads(header)
                            if isinstance(header_data, dict) and "binFile" in header_data:
                                if "filename" in header_data["binFile"]:
                                    original_filename = header_data["binFile"]["filename"]
                                    slugified_name = BinTextCommon.slugify(original_filename)
                                    renamed_path = os.path.join(output_file_dir, slugified_name)
                                    if os.path.exists(renamed_path):
                                        final_output_path = renamed_path
                        except (json.JSONDecodeError, KeyError):
                            pass

                # Read output file
                if not os.path.exists(final_output_path):
                    raise HTTPException(
                        status_code=500, detail="Output file not found after conversion"
                    )

                with open(final_output_path, "rb") as f:
                    output_content = f.read()

                # Determine filename for response - prioritize header filename
                output_filename = "output.bin"

                # First try to extract from provided header
                header_filename = extract_filename_from_header(header)

                # If no header provided, try to extract from file
                if not header_filename:
                    header_filename = extract_filename_from_text_file(input_path)

                # Use header filename if found, otherwise use uploaded filename or default
                if header_filename:
                    output_filename = header_filename
                else:
                    original_name = file.filename or "input.txt"
                    base_name = os.path.splitext(original_name)[0]
                    output_filename = f"{base_name}.bin"

                return StreamingResponse(
                    iter([output_content]),
                    media_type="application/octet-stream",
                    headers={"Content-Disposition": f'attachment; filename="{output_filename}"'},
                )
            finally:
                # Cleanup - check both possible paths
                if os.path.exists(output_path):
                    os.unlink(output_path)
                # Also check for renamed file
                output_file_dir = ntpath.dirname(output_path)
                if header:
                    try:
                        header_data = json.loads(header)
                        if isinstance(header_data, dict) and "binFile" in header_data:
                            if "filename" in header_data["binFile"]:
                                slugified_name = BinTextCommon.slugify(
                                    header_data["binFile"]["filename"]
                                )
                                renamed_path = os.path.join(output_file_dir, slugified_name)
                                if os.path.exists(renamed_path) and renamed_path != output_path:
                                    os.unlink(renamed_path)
                    except (json.JSONDecodeError, KeyError):
                        pass
        finally:
            # Cleanup
            if os.path.exists(input_path):
                os.unlink(input_path)


@router.post("/api/bin2text/text")
async def convert_bin2text_from_text(
    request: Bin2TextTextRequest,
):
    """Convert binary data (base64-encoded) to text format."""
    if request.format.upper() not in ["BINARY", "DECIMAL", "HEX", "ASCII", "BASE64"]:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid format: {request.format}. "
                "Must be one of: BINARY, DECIMAL, HEX, ASCII, BASE64"
            ),
        )

    # Decode base64 data
    try:
        binary_content = base64.b64decode(request.data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 data: {str(e)}")

    # Create temporary files
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as input_file:
        input_path = input_file.name
        try:
            # Write binary content to temp file
            input_file.write(binary_content)
            input_file.flush()

            # Create output temp file
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".txt", encoding="utf-8"
            ) as output_file:
                output_path = output_file.name

            try:
                # Perform conversion
                BinText.convert_bin2text(
                    binary_file_path=input_path,
                    text_file_path=output_path,
                    format=request.format.upper(),
                    delimiter=request.delimiter,
                    line_characters=request.line_characters,
                    show_header=request.show_header,
                )

                # Read output file
                with open(output_path, "rb") as f:
                    output_content = f.read()

                output_filename = f"output.{request.format.lower()}.txt"

                return StreamingResponse(
                    iter([output_content]),
                    media_type="text/plain",
                    headers={"Content-Disposition": f'attachment; filename="{output_filename}"'},
                )
            finally:
                # Cleanup
                if os.path.exists(output_path):
                    os.unlink(output_path)
        finally:
            # Cleanup
            if os.path.exists(input_path):
                os.unlink(input_path)


@router.post("/api/text2bin/text")
async def convert_text2bin_from_text(
    request: Text2BinTextRequest,
):
    """Convert text content to binary format."""
    # For web API, we disable rename_file to avoid interactive prompts
    # We'll handle filename in response headers instead
    actual_rename_file = False

    # Create temporary files
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".txt", encoding="utf-8"
    ) as input_file:
        input_path = input_file.name
        try:
            # Write text content to temp file
            input_file.write(request.text)
            input_file.flush()

            # Create output temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as output_file:
                output_path = output_file.name

            try:
                # Perform conversion (with rename_file=False to avoid interactive prompts)
                # Use non_interactive_mode to mock query_yes_no for validation prompts
                with non_interactive_mode():
                    BinText.convert_text2bin(
                        text_file_path=input_path,
                        output_file_path=output_path,
                        header=request.header,
                        rename_file=actual_rename_file,
                        default_output_filename=None,
                        force=True,
                    )

                # Check if file exists at original path (it might have been renamed)
                final_output_path = output_path
                if not os.path.exists(output_path):
                    # File might have been renamed - try to find it
                    output_file_dir = ntpath.dirname(output_path)
                    if request.header:
                        try:
                            header_data = json.loads(request.header)
                            if isinstance(header_data, dict) and "binFile" in header_data:
                                if "filename" in header_data["binFile"]:
                                    original_filename = header_data["binFile"]["filename"]
                                    slugified_name = BinTextCommon.slugify(original_filename)
                                    renamed_path = os.path.join(output_file_dir, slugified_name)
                                    if os.path.exists(renamed_path):
                                        final_output_path = renamed_path
                        except (json.JSONDecodeError, KeyError):
                            pass

                # Read output file
                if not os.path.exists(final_output_path):
                    raise HTTPException(
                        status_code=500, detail="Output file not found after conversion"
                    )

                with open(final_output_path, "rb") as f:
                    output_content = f.read()

                # Determine filename for response - prioritize header filename
                output_filename = "output.bin"

                # First try to extract from provided header parameter
                header_filename = extract_filename_from_header(request.header)

                # If no header parameter, try to extract from text content
                if not header_filename:
                    header_filename = extract_filename_from_text_file(input_path)

                # Use header filename if found
                if header_filename:
                    output_filename = header_filename

                return StreamingResponse(
                    iter([output_content]),
                    media_type="application/octet-stream",
                    headers={"Content-Disposition": f'attachment; filename="{output_filename}"'},
                )
            finally:
                # Cleanup - check both possible paths
                if os.path.exists(output_path):
                    os.unlink(output_path)
                # Also check for renamed file
                output_file_dir = ntpath.dirname(output_path)
                if request.header:
                    try:
                        header_data = json.loads(request.header)
                        if isinstance(header_data, dict) and "binFile" in header_data:
                            if "filename" in header_data["binFile"]:
                                slugified_name = BinTextCommon.slugify(
                                    header_data["binFile"]["filename"]
                                )
                                renamed_path = os.path.join(output_file_dir, slugified_name)
                                if os.path.exists(renamed_path) and renamed_path != output_path:
                                    os.unlink(renamed_path)
                    except (json.JSONDecodeError, KeyError):
                        pass
        finally:
            # Cleanup
            if os.path.exists(input_path):
                os.unlink(input_path)
