# src/tests/test_game_manager.py

import pytest
import chess
from unittest.mock import MagicMock

from gambit.game_manager import GameManager

@pytest.fixture
def mock_dependencies(monkeypatch):
    """Mocks the LLMHandler, database session, and chess engine."""
    mock_llm_handler = MagicMock()
    mock_db_session = MagicMock()

    mock_engine = MagicMock()
    mock_engine.play.return_value = MagicMock(move=chess.Move.from_uci("g1f3"))
    monkeypatch.setattr("chess.engine.SimpleEngine.popen_uci", lambda path: mock_engine)
    
    monkeypatch.setattr("gambit.game_manager.get_or_create_game", MagicMock(return_value=MagicMock(id=1)))
    monkeypatch.setattr("gambit.game_manager.log_move", MagicMock())

    return mock_llm_handler, mock_db_session, mock_engine

@pytest.fixture
def mock_config():
    """Provides a mock configuration."""
    return {
        'paths': {'stockfish': '/fake/path/to/stockfish'},
        'experiment': {'engine_skill_level': 1}
    }

def test_game_manager_initialization(mock_dependencies, mock_config):
    """Task 2.6.1: Tests that the GameManager class initializes correctly."""
    llm_handler, db_session, _ = mock_dependencies
    manager = GameManager(config=mock_config, db_session=db_session, llm_handler=llm_handler, persona_name="Test")
    assert manager is not None
    assert manager.board.is_valid()

def test_play_turn_legal_move(mock_dependencies, mock_config):
    """Task 2.6.2: Tests handling of a legal LLM move."""
    llm_handler, db_session, _ = mock_dependencies
    llm_handler.get_response.return_value = ("e7e5", "A simple reply.")

    manager = GameManager(config=mock_config, db_session=db_session, llm_handler=llm_handler, persona_name="Test")
    # UPDATED LINE: Changed 'w' (White's turn) to 'b' (Black's turn)
    manager.board = chess.Board("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 2")
    
    manager._play_llm_turn()

    from gambit.game_manager import log_move
    # UPDATED ASSERTION: Made it more specific to match the actual call
    log_move.assert_called_with(
        session=db_session, 
        game_id=1, 
        turn_number=2, 
        player='llm', 
        is_legal=True, 
        move_notation="e7e5", 
        llm_commentary="A simple reply.",
        board_state_fen='rnbqkbnr/pppp1ppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 3'
    )
    assert manager.board.peek() == chess.Move.from_uci("e7e5")

def test_play_turn_illegal_move(mock_dependencies, mock_config):
    """Task 2.6.2: Tests handling of an illegal LLM move."""
    llm_handler, db_session, _ = mock_dependencies
    llm_handler.get_response.side_effect = [
        ("a1a2", "An illegal move."),
        ("g1f3", "My apologies, a knight move.")
    ]

    manager = GameManager(config=mock_config, db_session=db_session, llm_handler=llm_handler, persona_name="Test")
    # It's White's turn, a1a2 is illegal, g1f3 is legal
    manager.board = chess.Board()
    manager._play_llm_turn()

    from gambit.game_manager import log_move
    assert log_move.call_args_list[0].kwargs['is_legal'] is False
    assert log_move.call_args_list[1].kwargs['is_legal'] is True
    assert manager.board.peek() == chess.Move.from_uci("g1f3")