# src/tests/test_turn_flow.py
import chess
from gambit.move_utils import apply_uci_once, IllegalMoveError

def test_apply_once_turn_flip():
    b = chess.Board()
    apply_uci_once(b, "e2e3")
    assert b.turn is chess.BLACK
    try:
        apply_uci_once(b, "e2e3")
        assert False, "should have raised"
    except IllegalMoveError:
        pass
