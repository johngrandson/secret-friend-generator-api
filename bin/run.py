import os
from subprocess import run

def start():
    """
    Starts the FastAPI application.
    - Uses Gunicorn with Uvicorn workers for production.
    - Uses Uvicorn with reload for development.
    Configurations are controlled via environment variables WORKERS, HOST, and PORT.
    """
    # Environment variables
    workers = os.getenv("WORKERS", "4")
    host = os.getenv("HOST", "0.0.0.0")
    port = os.getenv("PORT", "8000")
    environment = os.getenv("ENV", "development")  # Default to 'development'

    # Development mode with auto-reload
    if environment.lower() == "development":
        command = [
            "uvicorn",
            "src.app.main:app",  # Ensure this matches your FastAPI app entry point
            "--host", host,
            "--port", port,
            "--reload",
        ]
    # Production mode with Gunicorn
    else:
        command = [
            "gunicorn",
            "-w",
            workers,
            "-k",
            "uvicorn.workers.UvicornWorker",
            "-b",
            f"{host}:{port}",
            "src.app.main:app",  # Ensure this matches your FastAPI app entry point
        ]

    # Execute the command
    try:
        print(f"Starting server on {host}:{port} ({'Development' if environment.lower() == 'development' else 'Production'})...")
        run(command, check=True)
    except Exception as e:
        print(f"Failed to start the server: {e}")
        exit(1)
