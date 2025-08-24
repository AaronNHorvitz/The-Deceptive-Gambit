# src/gambit/move_utils.py
import chess

class IllegalMoveError(ValueError):
    pass

def apply_uci_once(board: chess.Board, uci: str) -> None:
    """
    Apply a single UCI move to `board` if and only if it's legal.
    Raise IllegalMoveError with a helpful message otherwise.
    """
    try:
        move = chess.Move.from_uci(uci)
    except Exception:
        raise IllegalMoveError(f"invalid UCI string '{uci}' (position: {board.fen()})")

    if move not in board.legal_moves:
        raise IllegalMoveError(f"illegal move {uci} in position {board.fen()}")

    board.push(move)
