import tomllib
from pathlib import Path

from fastapi import FastAPI

app = FastAPI()

PYPROJECT_PATH = Path(__file__).resolve().parent.parent / "pyproject.toml"


@app.get("/")
def send_hello():
    return {"message": "Hi there"}


@app.get("/health")
def health_service():
    return {"status": "ok"}


@app.get("/version")
def version_service():
    with PYPROJECT_PATH.open("rb") as f:
        pyproject = tomllib.load(f)
    return {"version": pyproject["project"]["version"]}
