"""Check that an engine's stdout is UCI and its moves are legal."""

import chess

from crossplay.uci_session import UciSession

PROMOTION_FEN = "8/P7/8/8/8/8/8/k6K w - - 0 1"
EN_PASSANT_FEN = "rnbqkbnr/ppp2ppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3"


def _board_after(position_command):
    tokens = position_command.split()
    board = chess.Board()
    index = 1
    if tokens[index] == "startpos":
        index += 1
    elif tokens[index] == "fen":
        index += 1
        fen = []
        while index < len(tokens) and tokens[index] != "moves":
            fen.append(tokens[index])
            index += 1
        board.set_fen(" ".join(fen))
    if index < len(tokens) and tokens[index] == "moves":
        for uci in tokens[index + 1 :]:
            board.push_uci(uci)
    return board


def _expect_legal(session, position_command):
    session.send(position_command)
    move, extras = session.go_line("go wtime 3000 btime 3000 winc 0 binc 0", 10)
    unexpected = [line for line in extras if not line.startswith("info")]
    if unexpected:
        raise AssertionError(session.name + " wrote " + repr(unexpected))
    board = _board_after(position_command)
    legal = list(board.legal_moves)
    if move == "0000":
        if legal:
            raise AssertionError(session.name + " returned 0000 with legal moves")
        return
    try:
        parsed = chess.Move.from_uci(move)
    except ValueError as exc:
        raise AssertionError(session.name + " returned " + move) from exc
    if parsed not in legal:
        raise AssertionError(f"{session.name} played illegal {move} in {board.fen()}")


def conform(session: UciSession):
    session.new_game()
    _expect_legal(session, "position fen " + PROMOTION_FEN)
    _expect_legal(session, "position startpos moves e2e4")
    _expect_legal(session, "position fen " + EN_PASSANT_FEN)
    session.new_game()
    _expect_legal(session, "position startpos")
