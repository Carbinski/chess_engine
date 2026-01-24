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
        if req.botId == "python":
            move, time_taken, depth = get_python_move(req.fen)
        elif req.botId == "java":
            move, time_taken, depth = get_java_move(req.fen)
        else:
            raise HTTPException(status_code=400, detail="Invalid botId")

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
            {"id": "python", "name": "Python Bot (FastV4)"},
            {"id": "java", "name": "Java Bot (BotV2)"}
        ]
    }
