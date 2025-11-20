# Docker Setup for BinTextTools

This directory contains Docker configuration files for building and running the BinTextTools FastAPI web application.

## Files

- `Dockerfile` - Multi-stage Docker build configuration
- `docker-compose.yml` - Docker Compose configuration
- `.dockerignore` - Files to exclude from Docker build context

## Usage

### Building the Docker Image

From the project root:

```bash
make docker-build
```

Or manually:

```bash
docker build -f infra/docker/Dockerfile -t bintexttools:latest .
```

### Running with Docker Compose

Start the web application:

```bash
make compose-up
```

Or manually:

```bash
docker compose -f infra/docker/docker-compose.yml up -d
```

The web application will be available at: http://localhost:8000

Stop the container:

```bash
make compose-down
```

Or manually:

```bash
docker compose -f infra/docker/docker-compose.yml down
```

### Accessing the Web Application

Once the container is running:

- **Web UI**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Viewing Logs

```bash
docker logs -f bintexttools-web
```

## Image Details

- **Base Image**: `python:3.14-slim`
- **Package Manager**: `uv` (installed from official image)
- **User**: Runs as non-root user (`appuser`)
- **Working Directory**: `/app/infra/web`
- **Port**: `8000`

