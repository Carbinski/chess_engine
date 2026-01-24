"use client";

import { useState, useEffect } from "react";
import { Chess } from "chess.js";
import { Chessboard } from "react-chessboard";

export default function ChessGame() {
    const [game, setGame] = useState(new Chess());
    const [botId, setBotId] = useState("python");
    const [loading, setLoading] = useState(false);
    const [playerColor, setPlayerColor] = useState<'w' | 'b'>('w');
    const [lastMove, setLastMove] = useState<{ from: string, to: string } | null>(null);
    const [botStats, setBotStats] = useState<{ time: number, depth: number } | null>(null);

    async function makeBotMove(currentFen: string) {
        setLoading(true);
        try {
            const response = await fetch("http://127.0.0.1:8000/move", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ fen: currentFen, botId }),
            });

            if (!response.ok) {
                throw new Error("Failed to fetch move");
            }

            const data = await response.json();
            console.log("Bot move UCI:", data.move);

            // Update bot stats
            if (data.time !== undefined && data.depth !== undefined) {
                setBotStats({ time: data.time, depth: data.depth });
            }

            setGame((current) => {
                const nextGame = new Chess(current.fen());
                // Parse UCI string (e.g. "e2e4", "a7a8q")
                const uci = data.move;
                if (!uci) return nextGame; // Game might be over or bot returned null

                const from = uci.substring(0, 2);
                const to = uci.substring(2, 4);
                const promotion = uci.length > 4 ? uci.substring(4, 5) : undefined;

                setLastMove({ from, to });

                try {
                    const result = nextGame.move({ from, to, promotion });
                    if (!result) console.error("Bot move invalid:", uci);
                } catch (e) {
                    console.error("Bot move failed:", e);
                }
                return nextGame;
            });

        } catch (error) {
            console.error("Error making bot move:", error);
            alert("Bot failed to move. See console for details.");
        } finally {
            setLoading(false);
        }
    }

    // Trigger bot move if it's bot's turn
    useEffect(() => {
        if (!loading && !game.isGameOver() && game.turn() !== playerColor) {
            makeBotMove(game.fen());
        }
    }, [game, playerColor, loading]);

    function onDrop(sourceSquare: string, targetSquare: string) {
        if (loading) return false;
        if (game.turn() !== playerColor) return false;

        // 1. Create a potential new game state to validate move synchronously
        const gameCopy = new Chess(game.fen());
        let move = null;
        try {
            move = gameCopy.move({
                from: sourceSquare,
                to: targetSquare,
                promotion: "q", // always promote to queen for simplicity
            });
        } catch (e) {
            // invalid move
            console.log("Invalid move attempt", e);
        }

        if (move === null) return false;

        // 2. Valid move: Update state
        setGame(gameCopy);

        // 3. check if game is over
        if (gameCopy.isGameOver()) {
            return true;
        }

        // Trigger bot move handled by useEffect/render logic above or explicit call here?
        // Actually, better to just let the update trigger it, but since we are inside onDrop, 
        // we can just leave it to the condition above? 
        // Wait, the condition above is inside the component body, so it runs on render. 
        // When setGame(gameCopy) happens, re-render occurs, condition passes, bot moves.
        // So we don't need explicit setTimeout here anymore.

        // Update highlight for player move
        setLastMove({ from: sourceSquare, to: targetSquare });

        return true;
    }

    return (
        <div className="flex flex-col items-center gap-4 max-w-xl w-full">
            <div className="flex gap-4 items-center flex-wrap justify-center">
                <div className="flex flex-col items-start">
                    <label className="font-bold text-white text-sm mb-1">Select Bot:</label>
                    <select
                        value={botId}
                        onChange={(e) => setBotId(e.target.value)}
                        className="p-2 rounded bg-gray-800 text-white border border-gray-600"
                    >
                        <option value="python">Python Bot (FastV4)</option>
                        <option value="java">Java Bot (BotV2)</option>
                    </select>
                </div>

                <div className="flex flex-col items-start">
                    <label className="font-bold text-white text-sm mb-1">Play As:</label>
                    <select
                        value={playerColor}
                        onChange={(e) => {
                            setPlayerColor(e.target.value as 'w' | 'b');
                            setGame(new Chess()); // Reset game on side change
                            setBotStats(null);
                            setLastMove(null);
                        }}
                        className="p-2 rounded bg-gray-800 text-white border border-gray-600"
                    >
                        <option value="w">White</option>
                        <option value="b">Black</option>
                    </select>
                </div>
            </div>

            <div className="w-full aspect-square">
                <Chessboard
                    options={{
                        position: game.fen(),
                        boardOrientation: playerColor === 'w' ? 'white' : 'black',
                        onPieceDrop: (args) => {
                            const { sourceSquare, targetSquare } = args;
                            if (!targetSquare) return false;
                            return onDrop(sourceSquare, targetSquare);
                        },
                        squareStyles: lastMove ? {
                            [lastMove.from]: { backgroundColor: 'rgba(255, 255, 0, 0.4)' },
                            [lastMove.to]: { backgroundColor: 'rgba(255, 255, 0, 0.4)' }
                        } : {}
                    }}
                />
            </div>

            <div className="text-white font-bold text-lg flex flex-col items-center">
                <div>
                    {loading ? "Bot is thinking..." :
                        game.isCheckmate() ? (game.turn() === playerColor ? "Checkmate! You Lost!" : "Checkmate! You Win!") :
                            game.isDraw() ? "Draw!" :
                                game.isGameOver() ? "Game Over" :
                                    game.turn() === playerColor ? "Your Turn" : "Bot's Turn"}
                </div>
                {botStats && (
                    <div className="text-sm text-gray-400 mt-2">
                        Last Move: {botStats.time.toFixed(2)}s | Depth: {botStats.depth}
                    </div>
                )}
            </div>

            <button
                onClick={() => setGame(new Chess())}
                className="px-4 py-2 bg-red-600 rounded text-white font-bold hover:bg-red-700"
            >
                Reset Game
            </button>
        </div>
    );
}
