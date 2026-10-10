import chess
import chess.svg

board = chess.Board()

print(board.legal_moves)

print(board.push_san("e4"))

chess.svg.board(
    board=board, 
    orientation=chess.WHITE
)

board = chess.Board("8/8/8/8/4N3/8/8/8 w - - 0 1")

chess.svg.board(
    board,
    fill=dict.fromkeys(board.attacks(chess.E4), "#cc0000cc"),
    arrows=[chess.svg.Arrow(chess.E4, chess.F6, color="#0000cccc")],
    squares=chess.SquareSet(chess.BB_DARK_SQUARES & chess.BB_FILE_B),
    size=350,
)  