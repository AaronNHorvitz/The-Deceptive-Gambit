# src/tests/test_game_manager.py

import pytest
import chess
from unittest.mock import MagicMock

from gambit import database
from gambit.game_manager import GameManager


@pytest.fixture
def mock_dependencies(monkeypatch):
    mock_llm_handler, mock_db_session, mock_engine = (
        MagicMock(),
        MagicMock(),
        MagicMock(),
    )
    mock_engine.play.return_value = MagicMock(move=chess.Move.from_uci("g1f3"))
    monkeypatch.setattr("chess.engine.SimpleEngine.popen_uci", lambda path: mock_engine)
    monkeypatch.setattr(
        database, "get_or_create_game", MagicMock(return_value=MagicMock(id=1))
    )
    monkeypatch.setattr(database, "log_move", MagicMock())
    return mock_llm_handler, mock_db_session, mock_engine


@pytest.fixture
def mock_config():
    return {
        "paths": {"stockfish": "/fake/path/to/stockfish"},
        "experiment": {"engine_skill_level": 1},
        "personas": {"Test": {"system_prompt": "Test prompt"}},
    }


def test_game_manager_initialization(mock_dependencies, mock_config):
    llm_handler, db_session, _ = mock_dependencies
    manager = GameManager(
        config=mock_config,
        db_session=db_session,
        llm_handler=llm_handler,
        persona_name="Test",
    )
    assert manager is not None
    assert manager.board.fen() == chess.STARTING_FEN


def test_play_turn_legal_move(mock_dependencies, mock_config):
    llm_handler, db_session, _ = mock_dependencies
    llm_handler.get_response.return_value = ("e7e5", "A simple reply.")

    # After 1.e4, Black to move
    starting_fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"

    manager = GameManager(
        config=mock_config,
        db_session=db_session,
        llm_handler=llm_handler,
        persona_name="Test",
        starting_fen=starting_fen,
        llm_color=chess.BLACK,
    )
    pre_move_fen = manager.board.fen()
    manager._play_llm_turn()

    database.log_move.assert_called_with(
        session=db_session,
        game_id=1,
        turn_number=2,
        player="llm",
        is_legal=True,
        move_notation="e7e5",
        llm_commentary="A simple reply.",
        board_state_fen=pre_move_fen,
    )
    # Board after 1.e4 e5
    assert (
        manager.board.fen()
        == "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
    )


def test_play_turn_illegal_move(mock_dependencies, mock_config):
    llm_handler, db_session, _ = mock_dependencies
    llm_handler.get_response.side_effect = [
        ("a1a2", "An illegal move."),  # Illegal rook move
        ("g1f3", "My apologies, a knight move."),  # Legal knight move
    ]
    starting_fen = chess.STARTING_FEN  # Normal initial board, White to move

    manager = GameManager(
        config=mock_config,
        db_session=db_session,
        llm_handler=llm_handler,
        persona_name="Test",
        starting_fen=starting_fen,
        llm_color=chess.WHITE,
    )
    manager._play_llm_turn()

    # First log: illegal
    assert database.log_move.call_args_list[0].kwargs["is_legal"] is False
    # Second log: legal
    assert database.log_move.call_args_list[1].kwargs["is_legal"] is True
    # Board now has the knight on f3
    assert manager.board.peek() == chess.Move.from_uci("g1f3")
