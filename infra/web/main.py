"""
Entry point for the BinTextTools web application.
"""

from app.config import settings
from app.main import app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)
