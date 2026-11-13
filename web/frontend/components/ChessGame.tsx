"use client";

import { useEffect, useRef, useState } from "react";
import { Chess, type Square } from "chess.js";
import { Chessboard } from "react-chessboard";

const API = "http://127.0.0.1:8000";
const START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

type Seat = { id: string; name: string };

type Snapshot = {
    id: string;
    fen: string;
    white: Seat;
    black: Seat;
    whiteMs: number;
    blackMs: number;
    ticking: "w" | "b" | null;
    initialMs: number;
    incrementMs: number;
    moves: string[];
    lastMove: { from: string; to: string } | null;
    result: string;
    reason: string;
    thinking: boolean;
    stateId: number;
    turn: "w" | "b";
};

type Bot = { id: string; name: string; language: string };

function formatTime(ms: number) {
    const totalSeconds = Math.ceil(Math.max(0, ms) / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function promotionUci(fen: string, from: string, to: string) {
    const piece = new Chess(fen).get(from as never);
    if (piece && piece.type === "p" && (to[1] === "8" || to[1] === "1")) {
        return from + to + "q";
    }
    return from + to;
}

function resultText(snap: Snapshot) {
    if (snap.result === "*") {
        const seat = snap.turn === "w" ? snap.white : snap.black;
        if (snap.thinking || seat.id !== "human") {
            return `${seat.name} is thinking`;
        }
        return "Your turn";
    }
    const winner = snap.result === "1-0" ? snap.white.name : snap.result === "0-1" ? snap.black.name : "";
    if (snap.result === "1/2-1/2") {
        return `Draw${snap.reason ? ` (${snap.reason})` : ""}`;
    }
    return `${winner} wins${snap.reason ? ` (${snap.reason})` : ""}`;
}

export default function ChessGame() {
    const [bots, setBots] = useState<Bot[]>([]);
    const [whiteId, setWhiteId] = useState("human");
    const [blackId, setBlackId] = useState("python_random");
    const [initialMs, setInitialMs] = useState(60000);
    const [incrementMs, setIncrementMs] = useState(0);
    const [snap, setSnap] = useState<Snapshot | null>(null);
    const [receivedAt, setReceivedAt] = useState(Date.now());
    const [now, setNow] = useState(Date.now());
    const [error, setError] = useState<string | null>(null);
    const [busy, setBusy] = useState(false);
    const [selected, setSelected] = useState<string | null>(null);
    const request = useRef(0);
    const retiredGameIds = useRef(new Set<string>());

    useEffect(() => {
        let cancelled = false;
        fetch(`${API}/bots`)
            .then((response) => {
                if (!response.ok) throw new Error("Could not load engines");
                return response.json();
            })
            .then((data) => {
                if (!cancelled) setBots(data.bots);
            })
            .catch((exc: Error) => {
                if (!cancelled) setError(exc.message);
            });
        return () => {
            cancelled = true;
        };
    }, []);

    const gameId = snap?.id ?? null;
    const playing = snap !== null && snap.result === "*";

    useEffect(() => {
        setSelected(null);
    }, [snap?.fen, snap?.id]);

    useEffect(() => {
        if (!playing) return;
        const timer = setInterval(() => setNow(Date.now()), 100);
        return () => clearInterval(timer);
    }, [playing]);

    useEffect(() => {
        if (!playing || !gameId) return;
        const timer = setInterval(() => {
            const ticket = request.current;
            fetch(`${API}/games/${gameId}`)
                .then(async (response) => {
                    if (ticket !== request.current || !response.ok) return;
                    const data = (await response.json()) as Snapshot;
                    if (ticket !== request.current || retiredGameIds.current.has(data.id)) return;
                    setSnap(data);
                    const stamp = Date.now();
                    setReceivedAt(stamp);
                    setNow(stamp);
                })
                .catch(() => undefined);
        }, 250);
        return () => clearInterval(timer);
    }, [playing, gameId]);

    async function accept(call: Promise<Response>) {
        const ticket = ++request.current;
        const response = await call;
        if (ticket < request.current) return null;
        if (!response.ok) {
            let detail = response.statusText;
            try {
                const body = await response.json();
                detail = body.detail || detail;
            } catch {
                detail = await response.text();
            }
            throw new Error(typeof detail === "string" ? detail : "Request failed");
        }
        const data = (await response.json()) as Snapshot;
        if (ticket < request.current) return null;
        if (retiredGameIds.current.has(data.id)) return null;
        setSnap(data);
        setReceivedAt(Date.now());
        setNow(Date.now());
        return data;
    }

    async function startGame() {
        setError(null);
        setBusy(true);
        request.current += 1;
        const previous = snap?.id;
        if (previous) retiredGameIds.current.add(previous);
        try {
            if (previous) {
                await fetch(`${API}/games/${previous}`, { method: "DELETE" });
            }
            await accept(
                fetch(`${API}/games`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ white: whiteId, black: blackId, initialMs, incrementMs }),
                }),
            );
        } catch (exc) {
            setError(exc instanceof Error ? exc.message : "Could not start the game");
        } finally {
            setBusy(false);
        }
    }

    function liveMs(base: number, side: "w" | "b") {
        if (!snap || snap.result !== "*" || snap.ticking !== side) return base;
        return Math.max(0, base - (now - receivedAt));
    }

    const fen = snap?.fen ?? START_FEN;
    const orientation =
        blackId === "human" && whiteId !== "human" ? "black" : "white";
    const turnSeat = snap ? (snap.turn === "w" ? snap.white : snap.black) : null;
    const humanTurn = Boolean(snap && snap.result === "*" && turnSeat?.id === "human");

    function onSquareClick(square: string) {
        if (!snap || !humanTurn || busy) return;
        if (selected && selected !== square) {
            const moved = onDrop(selected, square);
            setSelected(null);
            if (moved) return;
        }
        const piece = new Chess(snap.fen).get(square as Square);
        if (piece && piece.color === snap.turn) {
            setSelected(square);
        } else {
            setSelected(null);
        }
    }

    function onDrop(sourceSquare: string, targetSquare: string) {
        if (!snap || !humanTurn || busy) return false;
        const uci = promotionUci(snap.fen, sourceSquare, targetSquare);
        const probe = new Chess(snap.fen);
        const from = uci.slice(0, 2);
        const to = uci.slice(2, 4);
        const promotion = uci.length > 4 ? uci.slice(4) : undefined;
        try {
            if (!probe.move({ from, to, promotion })) return false;
        } catch {
            return false;
        }
        setBusy(true);
        accept(
            fetch(`${API}/games/${snap.id}/move`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ uci }),
            }),
        )
            .catch((exc: Error) => setError(exc.message))
            .finally(() => setBusy(false));
        return true;
    }

    const languages = ["python", "java", "cpp"].filter((language) =>
        bots.some((bot) => bot.language === language),
    );

    function options(includeHuman: boolean) {
        return (
            <>
                {includeHuman && <option value="human">Human</option>}
                {languages.map((language) => (
                    <optgroup key={language} label={language === "cpp" ? "C++" : language[0].toUpperCase() + language.slice(1)}>
                        {bots
                            .filter((bot) => bot.language === language)
                            .map((bot) => (
                                <option key={bot.id} value={bot.id}>
                                    {bot.name}
                                </option>
                            ))}
                    </optgroup>
                ))}
            </>
        );
    }

    const whiteMs = snap ? liveMs(snap.whiteMs, "w") : initialMs;
    const blackMs = snap ? liveMs(snap.blackMs, "b") : initialMs;
    const lastMove = snap?.lastMove;

    return (
        <div className="flex w-full max-w-4xl flex-col items-center gap-4">
            <div className="flex flex-wrap items-end justify-center gap-4">
                <label className="flex flex-col items-start text-sm text-white">
                    White
                    <select
                        value={whiteId}
                        onChange={(event) => setWhiteId(event.target.value)}
                        className="mt-1 rounded border border-gray-600 bg-gray-800 p-2 text-white"
                    >
                        {options(true)}
                    </select>
                </label>
                <label className="flex flex-col items-start text-sm text-white">
                    Black
                    <select
                        value={blackId}
                        onChange={(event) => setBlackId(event.target.value)}
                        className="mt-1 rounded border border-gray-600 bg-gray-800 p-2 text-white"
                    >
                        {options(true)}
                    </select>
                </label>
                <label className="flex flex-col items-start text-sm text-white">
                    Clock
                    <select
                        value={initialMs}
                        onChange={(event) => setInitialMs(Number(event.target.value))}
                        className="mt-1 rounded border border-gray-600 bg-gray-800 p-2 text-white"
                    >
                        <option value={60000}>1 minute</option>
                        <option value={180000}>3 minutes</option>
                        <option value={300000}>5 minutes</option>
                        <option value={600000}>10 minutes</option>
                    </select>
                </label>
                <label className="flex flex-col items-start text-sm text-white">
                    Increment
                    <select
                        value={incrementMs}
                        onChange={(event) => setIncrementMs(Number(event.target.value))}
                        className="mt-1 rounded border border-gray-600 bg-gray-800 p-2 text-white"
                    >
                        <option value={0}>None</option>
                        <option value={1000}>1 second</option>
                        <option value={2000}>2 seconds</option>
                    </select>
                </label>
                <button
                    onClick={() => void startGame()}
                    disabled={busy}
                    className="rounded bg-emerald-700 px-4 py-2 font-bold text-white hover:bg-emerald-600 disabled:opacity-50"
                >
                    {snap ? "New game" : "Start game"}
                </button>
            </div>

            <div className="flex w-full flex-col items-start justify-center gap-6 lg:flex-row">
                <div className="flex w-full max-w-xl flex-col gap-3">
                    <div className="flex justify-between px-1 font-mono text-xl font-bold text-white">
                        <div className={`rounded p-2 ${snap?.ticking === "w" ? "bg-yellow-600" : "bg-gray-700"}`}>
                            {snap?.white.name ?? "White"}: {formatTime(whiteMs)}
                        </div>
                        <div className={`rounded p-2 ${snap?.ticking === "b" ? "bg-yellow-600" : "bg-gray-700"}`}>
                            {snap?.black.name ?? "Black"}: {formatTime(blackMs)}
                        </div>
                    </div>
                    <div className="aspect-square w-full">
                        <Chessboard
                            options={{
                                position: fen,
                                boardOrientation: orientation,
                                allowDragging: humanTurn,
                                onPieceDrop: ({ sourceSquare, targetSquare }) => {
                                    if (!targetSquare) return false;
                                    return onDrop(sourceSquare, targetSquare);
                                },
                                onSquareClick: ({ square }) => onSquareClick(square),
                                squareStyles: {
                                    ...(lastMove
                                        ? {
                                              [lastMove.from]: { backgroundColor: "rgba(255, 255, 0, 0.4)" },
                                              [lastMove.to]: { backgroundColor: "rgba(255, 255, 0, 0.4)" },
                                          }
                                        : {}),
                                    ...(selected
                                        ? { [selected]: { backgroundColor: "rgba(20, 120, 220, 0.55)" } }
                                        : {}),
                                },
                            }}
                        />
                    </div>
                    <div className="text-center text-lg font-bold text-white">
                        {snap ? resultText(snap) : "Choose two seats and start a game."}
                    </div>
                    {error && <div className="text-center text-sm text-red-400">{error}</div>}
                </div>
                <ol className="max-h-[32rem] w-full overflow-auto rounded bg-gray-800 p-4 text-white lg:w-56">
                    {snap?.moves.length ? (
                        snap.moves.map((move, index) => (
                            <li key={`${index}-${move}`} className="font-mono">
                                {index % 2 === 0 ? `${index / 2 + 1}. ${move}` : `    ${move}`}
                            </li>
                        ))
                    ) : (
                        <li className="text-gray-400">Moves will show up here.</li>
                    )}
                </ol>
            </div>
        </div>
    );
}
