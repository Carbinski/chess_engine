from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from bot_manager import get_python_move, get_java_move

app = FastAPI()

# Allow CORS for local development
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

@app.post("/move")
def get_move(req: MoveRequest):
    try:
        print(f"Received request: {req}")
        
        if req.botId.startswith("python"):
            move, time_taken, depth = get_python_move(req.fen, req.botId)
        elif req.botId.startswith("java"):
            move, time_taken, depth = get_java_move(req.fen, req.botId)
        # Backward compatibility
        elif req.botId == "python":
             move, time_taken, depth = get_python_move(req.fen, "python_fast_v4")
        elif req.botId == "java":
             move, time_taken, depth = get_java_move(req.fen, "java_bot_v2")
        else:
            raise HTTPException(status_code=400, detail=f"Invalid botId: {req.botId}")

        if move is None:
             print("No move returned (Game Over or No Move)")
             return {"move": None, "time": 0, "depth": 0}
        
        print(f"Returning move: {move} with time: {time_taken:.4f}s and depth: {depth}")
        return {"move": move, "time": time_taken, "depth": depth}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bots")
def list_bots():
    return {
        "bots": [
            {"id": "python_random", "name": "Python: Random"},
            {"id": "python_aggressive", "name": "Python: Aggressive"},
            {"id": "python_dumb_eval", "name": "Python: DumbEval"},
            {"id": "python_basic_search", "name": "Python: Basic Search"},
            {"id": "python_fast_v2", "name": "Python: FastBotV2"},
            {"id": "python_midgame_v1", "name": "Python: MidGameBotV1"},
            {"id": "java_basic_v3", "name": "Java: BasicBot_V3"},
            {"id": "java_fast_v2", "name": "Java: FastBot_V2"},
            {"id": "java_bot_v2", "name": "Java: Bot_V2"},
        ]
    }
