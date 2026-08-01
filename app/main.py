import tomllib
from pathlib import Path

from fastapi import FastAPI

app = FastAPI()


def _load_version() -> str:
    pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]


@app.get("/")
def send_hello():
    return {"message": "Hi there"}


@app.get("/health")
def health_service():
    return {"status": "ok"}


@app.get("/version")
def version_service():
    return {"version": _load_version()}
