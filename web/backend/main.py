import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from crossplay.catalog import HUMAN, get, public_list
from crossplay.live import GameManager
from crossplay.uci_session import EngineError, UciSession

manager = GameManager()


@asynccontextmanager
async def lifespan(_app):
    yield
    manager.close_all()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MoveRequest(BaseModel):
    fen: str
    botId: str
    timeLimit: int = 5000


class GameRequest(BaseModel):
    white: str
    black: str
    initialMs: int = Field(default=60000, ge=200, le=60 * 60 * 1000)
    incrementMs: int = Field(default=0, ge=0, le=60 * 1000)


class HumanMove(BaseModel):
    uci: str


def _bad_engine(exc):
    raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/bots")
def list_bots():
    return {"bots": public_list()}


@app.post("/games")
def create_game(req: GameRequest):
    try:
        if req.white != HUMAN:
            get(req.white)
        if req.black != HUMAN:
            get(req.black)
        game = manager.create(req.white, req.black, req.initialMs, req.incrementMs)
    except (ValueError, EngineError) as exc:
        _bad_engine(exc)
    return game.snapshot()


@app.get("/games/{game_id}")
def read_game(game_id: str):
    try:
        game = manager.get(game_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="game not found") from None
    return game.snapshot()


@app.post("/games/{game_id}/move")
def play_move(game_id: str, req: HumanMove):
    try:
        game = manager.get(game_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="game not found") from None
    try:
        game.human_move(req.uci)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return game.snapshot()


@app.delete("/games/{game_id}")
def delete_game(game_id: str):
    try:
        manager.close(game_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="game not found") from None
    return {"ok": True}


@app.post("/move")
def get_move(req: MoveRequest):
    """One-shot UCI query kept for the older bot checker."""
    try:
        spec = get(req.botId)
    except ValueError as exc:
        _bad_engine(exc)
    session = None
    try:
        session = UciSession(spec["command"], spec["name"])
        session.new_game()
        import time

        started = time.perf_counter()
        move, _extras = session.go(
            req.fen,
            req.timeLimit,
            req.timeLimit,
            0,
            0,
            timeout=req.timeLimit / 1000 + 5,
        )
        elapsed = time.perf_counter() - started
    except EngineError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if session is not None:
            session.close()
    if move == "0000":
        return {"move": None, "time": elapsed, "depth": 0}
    return {"move": move, "time": elapsed, "depth": 0}
