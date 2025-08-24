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

def is_move_color_correct(board: chess.Board, uci: str) -> bool:
    """
    Return True iff the piece on the 'from' square belongs to the side to move.
    If parsing fails or square empty, return False.
    """
    try:
        mv = chess.Move.from_uci(uci)
    except Exception:
        return False
    piece = board.piece_at(mv.from_square)
    
    return piece is not None and piece.color == board.turn
