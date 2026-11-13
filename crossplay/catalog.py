"""The one engine list. The CLI and the web both read engines/catalog.json."""

import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "engines" / "catalog.json"
HUMAN = "human"

_JAVA_CLASS = ROOT / "engines" / "java" / "target" / "classes" / "org" / "UciBot.class"


def _java_classpath():
    jar = ROOT / "engines" / "java" / "libs" / "chesslib-1.3.3.jar"
    classes = ROOT / "engines" / "java" / "target" / "classes"
    return os.pathsep.join((str(jar), str(classes)))


def _resolve(token):
    if token == "{python}":
        return sys.executable
    if token == "{java}":
        return shutil.which("java") or "java"
    if token == "{java_cp}":
        return _java_classpath()
    if token == "{root}":
        return str(ROOT)
    if token.startswith("{root}/"):
        return str(ROOT / token[len("{root}/") :])
    return token


def _load():
    with CATALOG_PATH.open() as handle:
        payload = json.load(handle)
    engines = []
    for entry in payload["engines"]:
        command = [_resolve(part) for part in entry["command"]]
        engines.append({
            "id": entry["id"],
            "name": entry["name"],
            "language": entry["language"],
            "command": command,
        })
    return engines


def _executable(command, language):
    program = command[0]
    if os.path.isabs(program):
        if not (os.path.isfile(program) and os.access(program, os.X_OK)):
            return False
    elif shutil.which(program) is None:
        return False
    if language == "java" and not _JAVA_CLASS.is_file():
        return False
    return True


def engines(available_only=True):
    rows = _load()
    if not available_only:
        return rows
    return [row for row in rows if _executable(row["command"], row["language"])]


def get(engine_id):
    if engine_id == HUMAN:
        return {"id": HUMAN, "name": "Human", "language": "human", "command": None}
    for row in _load():
        if row["id"] == engine_id:
            if not _executable(row["command"], row["language"]):
                raise ValueError(f"{engine_id} is not available. Build it, then try again.")
            return row
    raise ValueError(f"Unknown engine: {engine_id}")


def public_list():
    return [
        {"id": row["id"], "name": row["name"], "language": row["language"]}
        for row in engines(available_only=True)
    ]
