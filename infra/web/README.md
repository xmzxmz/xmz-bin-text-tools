# BinTextTools Web Application

FastAPI web application providing a user-friendly interface and REST API for binary and text conversion tools.

## Features

- **Web UI**: Bootstrap 5-based interface for easy file conversion
- **REST API**: Full API access to all conversion tools
- **Interactive Documentation**: Swagger UI and ReDoc for API exploration
- **File Upload**: Direct file upload and download via web interface

## Project Structure

```
infra/web/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── api/                 # API routers
│   │   ├── __init__.py
│   │   ├── health.py        # Health check endpoint
│   │   └── converters.py    # Conversion endpoints
│   ├── templates/           # HTML templates
│   │   └── index.html       # Main UI page
│   └── static/              # Static files (CSS, JS, images)
└── README.md
```

## Running the Application

### Using Make (Recommended)

**Development mode** (with auto-reload):
```bash
make web-dev
```

**Production mode**:
```bash
make web
```

### Using Docker

```bash
make docker-build
make compose-up
```

The application will be available at http://localhost:8000

### Manual Run

```bash
# Activate virtual environment
source .venv/bin/activate

# Set Python path
export PYTHONPATH="src:infra/web"

# Run uvicorn
cd infra/web
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### Web UI
- `GET /` - Main web interface with Bootstrap 5 UI

### Conversion APIs
- `POST /api/bin2text` - Convert binary file to text format
- `POST /api/text2bin` - Convert text file to binary format

### Utility
- `GET /health` - Health check endpoint

### Documentation
- `GET /docs` - Swagger UI (interactive API documentation)
- `GET /redoc` - ReDoc (alternative API documentation)
- `GET /openapi.json` - OpenAPI schema

## API Usage Examples

### Convert Binary to Text (cURL)

```bash
curl -X POST "http://localhost:8000/api/bin2text" \
  -F "file=@input.bin" \
  -F "format=HEX" \
  -F "line_characters=0" \
  -F "show_header=true" \
  --output output.txt
```

### Convert Text to Binary (cURL)

```bash
curl -X POST "http://localhost:8000/api/text2bin" \
  -F "file=@input.txt" \
  --output output.bin
```

### Using Python requests

```python
import requests

# Binary to Text
with open('input.bin', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/bin2text',
        files={'file': f},
        data={
            'format': 'HEX',
            'line_characters': 0,
            'show_header': True
        }
    )
    with open('output.txt', 'wb') as out:
        out.write(response.content)
```

## Configuration

Configuration is managed through environment variables with the `BINTEXT_` prefix:

- `BINTEXT_APP_TITLE` - Application title (default: "BinTextTools")
- `BINTEXT_APP_DESCRIPTION` - Application description
- `BINTEXT_APP_VERSION` - Application version
- `BINTEXT_DOCS_URL` - Swagger UI URL (default: "/docs")
- `BINTEXT_REDOC_URL` - ReDoc URL (default: "/redoc")
- `BINTEXT_OPENAPI_URL` - OpenAPI schema URL (default: "/openapi.json")

## Development

The web application uses the same codebase as the CLI tools. The conversion logic is shared through the `bintexttools` package.

To add new features:

1. Add API endpoints in `src/app/api/`
2. Update the UI in `src/app/templates/index.html`
3. Add static files to `src/app/static/` if needed

## License

MIT License - see LICENSE file for details.

