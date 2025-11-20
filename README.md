# bintexttools

Tools for Binary and ASCII data conversion.

Tools which allow you to convert Binary data to ASCII and ASCII to Binary format.
They will allow you to keep printed version of data which need to be kept that way.

## Features

- Convert binary files to text format (HEX, BASE64, ASCII, DECIMAL, BINARY)
- Convert text files back to binary format
- Support for various output formats and delimiters
- Command-line tools: `bin2text` and `text2bin`

## Requirements

- Python 3.14.0+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

## Installation

### Using uv (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd xmz-bin-text-tools

# Install the package
uv sync

# Activate the virtual environment
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate  # On Windows
```

### Using pip

```bash
pip install bintexttools
```

## Project Structure

```
xmz-bin-text-tools/
├── pyproject.toml       # Project configuration
├── uv.lock              # Lock file for reproducible builds
├── README.md            # This file
├── LICENSE              # MIT License
├── src/                 # Source code
│   └── bintexttools/
│       ├── __init__.py
│       ├── bin2text.py  # Binary to text converter CLI
│       ├── text2bin.py  # Text to binary converter CLI
│       ├── bintextcommon/
│       │   ├── __init__.py
│       │   └── bin_text_common.py
│       └── bintexthelper/
│           ├── __init__.py
│           ├── bin_text.py
│           ├── bin2text_converter.py
│           ├── text2bin_converter.py
│           └── text_format.py
└── tests/               # Test suite
    └── __init__.py
```

## Usage

### Command Line Tools

#### Convert Binary to Text

```bash
bin2text -i input.bin -o output.txt -f HEX
```

Options:
- `-i, --binaryFilePath`: Input binary file (required)
- `-o, --textFilePath`: Output text file (optional, defaults to timestamp-based name)
- `-f, --format`: Output format - BINARY, DECIMAL, HEX, ASCII, BASE64 (default: HEX)
- `-d, --delimiter`: Data delimiter (optional)
- `-l, --lineCharacters`: Number of characters per line (default: 0)
- `--showHeader`: Show/add info header data (default: True)
- `-ll, --logging_level`: Logging level (CRITICAL, ERROR, WARNING, INFO, DEBUG)

#### Convert Text to Binary

```bash
text2bin -i input.txt -o output.bin --header '{"textFile":{"format":"HEX"}}'
```

Options:
- `-i, --textFilePath`: Input text file (required)
- `-o, --outputFilePath`: Output binary file (optional, defaults to timestamp-based name)
- `--header`: JSON header with format information (optional, auto-detected from file if present)
- `--renameFile/--no-renameFile`: Automatically rename output file to original name from header (default: rename)
- `--skip-rename`: Shortcut flag to disable renaming regardless of other options
- `--force/--no-force`: Continue conversion even if validation fails (default: stop on errors)
- `-ll, --logging_level`: Logging level (CRITICAL, ERROR, WARNING, INFO, DEBUG)

### Python API

```python
from bintexttools import bin2text, text2bin

# Convert binary to text
bin2text('input.bin', 'output.txt', format='HEX')

# Convert text to binary
text2bin('input.txt', 'output.bin', format='HEX')
```

## Development

### Setup Development Environment

```bash
# Install with development dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/
```

## License

MIT License - see LICENSE file for details.

## Author

Marcin Zelek (marcin.zelek@gmail.com)