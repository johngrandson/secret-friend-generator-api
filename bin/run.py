import os
from subprocess import run


def start():
    workers = os.getenv("WORKERS", "4")
    host = os.getenv("HOST", "0.0.0.0")
    port = os.getenv("PORT", "8000")
    environment = os.getenv("ENV", "development")

    if environment.lower() == "development":
        command = [
            "uvicorn",
            "src.app_main:app",
            "--host",
            host,
            "--port",
            port,
            "--reload",
        ]
    else:
        command = [
            "gunicorn",
            "-w",
            workers,
            "-k",
            "uvicorn.workers.UvicornWorker",
            "-b",
            f"{host}:{port}",
            "src.app_main:app",
        ]

    try:
        print(
            f"Starting server on {host}:{port} ({'Development' if environment.lower() == 'development' else 'Production'})..."
        )
        run(command, check=True)
    except Exception as e:
        print(f"Failed to start the server: {e}")
        exit(1)
