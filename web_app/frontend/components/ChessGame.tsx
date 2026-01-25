"use client";

import { useState, useEffect, useRef } from "react";
import { Chess, Move } from "chess.js";
import { Chessboard } from "react-chessboard";

export default function ChessGame() {
    const [game, setGame] = useState(new Chess());
    const [botId, setBotId] = useState("python_random");
    const [loading, setLoading] = useState(false);
    const [playerColor, setPlayerColor] = useState<'w' | 'b'>('w');
    const [lastMove, setLastMove] = useState<{ from: string, to: string } | null>(null);
    const [botStats, setBotStats] = useState<{ time: number, depth: number } | null>(null);

    // Time Control State
    const [gameTime, setGameTime] = useState(60000); // Default 1 minute
    const [whiteTime, setWhiteTime] = useState(60000);
    const [blackTime, setBlackTime] = useState(60000);
    const [gameStarted, setGameStarted] = useState(false); // Helper to track if clock should run for White

    // For non-timebots, this might still be used if we wanted to support fixed time, 
    // but for TimeBot we use gameTime. We can keep this state or repurpose UI.
    // The requirement says "instead of having an allotted time per move... there are two clocks".
    // So for TimeBot, we hide the invalid "Time Limit" and show "Game Time".

    async function makeBotMove(currentFen: string) {
        setLoading(true);
        try {
            // Determine time limit based on whose turn it is
            // If bot is playing, pass its remaining time
            const isWhiteTurn = game.turn() === 'w';
            const remainingTime = isWhiteTurn ? whiteTime : blackTime;

            const response = await fetch("http://127.0.0.1:8000/move", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    fen: currentFen,
                    botId,
                    timeLimit: remainingTime // Pass remaining game time
                }),
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

    // Timer Logic
    useEffect(() => {
        // If game is over, stop timer
        if (game.isGameOver() || (whiteTime <= 0) || (blackTime <= 0)) return;

        // If player is white, clock only starts after first move
        if (playerColor === 'w' && !gameStarted && game.turn() === 'w') {
            return;
        }

        const interval = setInterval(() => {
            if (game.turn() === 'w') {
                setWhiteTime((t) => Math.max(0, t - 100));
            } else {
                setBlackTime((t) => Math.max(0, t - 100));
            }
        }, 100);

        return () => clearInterval(interval);
    }, [game, whiteTime, blackTime, gameStarted, playerColor]);

    // Check for flags (timeout)
    useEffect(() => {
        if (whiteTime <= 0) {
            // White lost on time
        }
        if (blackTime <= 0) {
            // Black lost on time
        }
    }, [whiteTime, blackTime]);

    // Trigger bot move if it's bot's turn
    useEffect(() => {
        if (!loading && !game.isGameOver() && game.turn() !== playerColor) {
            // Check if time ran out
            if (playerColor === 'w' && blackTime <= 0) return;
            if (playerColor === 'b' && whiteTime <= 0) return;

            makeBotMove(game.fen());
        }
    }, [game, playerColor, loading, blackTime, whiteTime]); // Added timedeps to prevent move if OOT? 
    // Actually standard check inside effect is better.

    function onDrop(sourceSquare: string, targetSquare: string) {
        if (loading) return false;
        if (game.turn() !== playerColor) return false;
        if (whiteTime <= 0 || blackTime <= 0) return false;

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
        setGameStarted(true); // Player made a move, clock can start now (if white)

        // 3. check if game is over
        if (gameCopy.isGameOver()) {
            return true;
        }

        // Update highlight for player move
        setLastMove({ from: sourceSquare, to: targetSquare });

        return true;
    }

    // Helper to format time
    const formatTime = (ms: number) => {
        const totalSeconds = Math.ceil(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    };

    const resetGame = (newTime?: number) => {
        const t = newTime || gameTime;
        setGame(new Chess());
        setWhiteTime(t);
        setBlackTime(t);
        setGameStarted(false);
        setBotStats(null);
        setLastMove(null);
    };

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
                        <option value="python_random">Python: Random</option>
                        <option value="python_aggressive">Python: Aggressive</option>
                        <option value="python_dumb_eval">Python: DumbEval</option>
                        <option value="python_basic_search">Python: Basic Search</option>
                        <option value="python_fast_v2">Python: FastBotV2</option>
                        <option value="python_midgame_v1">Python: MidGameBotV1</option>
                        <option value="java_basic_v3">Java: BasicBot_V3</option>
                        <option value="java_fast_v2">Java: FastBot_V2</option>
                        <option value="java_bot_v2">Java: Bot_V2</option>
                        <option value="java_time_bot">Java: TimeBot V1</option>
                    </select>
                </div>

                {botId === "java_time_bot" && (
                    <div className="flex flex-col items-start">
                        <label className="font-bold text-white text-sm mb-1">Game Time:</label>
                        <select
                            value={gameTime}
                            onChange={(e) => {
                                const t = Number(e.target.value);
                                setGameTime(t);
                                resetGame(t);
                            }}
                            className="p-2 rounded bg-gray-800 text-white border border-gray-600"
                        >
                            <option value={60000}>1 Minute</option>
                            <option value={180000}>3 Minutes</option>
                            <option value={300000}>5 Minutes</option>
                            <option value={600000}>10 Minutes</option>
                        </select>
                    </div>
                )}

                <div className="flex flex-col items-start">
                    <label className="font-bold text-white text-sm mb-1">Play As:</label>
                    <select
                        value={playerColor}
                        onChange={(e) => {
                            setPlayerColor(e.target.value as 'w' | 'b');
                            resetGame(); // Reset game on side change
                        }}
                        className="p-2 rounded bg-gray-800 text-white border border-gray-600"
                    >
                        <option value="w">White</option>
                        <option value="b">Black</option>
                    </select>
                </div>
            </div>

            {/* Time Display */}
            <div className="flex justify-between w-full px-4 text-white font-mono font-bold text-xl">
                <div className={`p-2 rounded ${game.turn() === 'w' ? 'bg-yellow-600' : 'bg-gray-700'}`}>
                    White: {formatTime(whiteTime)}
                </div>
                <div className={`p-2 rounded ${game.turn() === 'b' ? 'bg-yellow-600' : 'bg-gray-700'}`}>
                    Black: {formatTime(blackTime)}
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
                        whiteTime <= 0 ? "timeout! black wins!" :
                            blackTime <= 0 ? "timeout! white wins!" :
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
                onClick={() => resetGame()}
                className="px-4 py-2 bg-red-600 rounded text-white font-bold hover:bg-red-700"
            >
                Reset Game
            </button>
        </div>
    );
}
