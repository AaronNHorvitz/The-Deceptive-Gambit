# src/tests/test_game_manager.py

import pytest
import chess
from unittest.mock import MagicMock

from gambit.game_manager import GameManager

@pytest.fixture
def mock_dependencies(monkeypatch):
    """Mocks the LLMHandler and database session."""
    mock_llm_handler = MagicMock()
    mock_db_session = MagicMock()
    
    # Mock the database functions
    monkeypatch.setattr("gambit.game_manager.get_or_create_game", MagicMock(return_value=MagicMock(id=1)))
    monkeypatch.setattr("gambit.game_manager.log_move", MagicMock())

    return mock_llm_handler, mock_db_session

@pytest.fixture
def mock_config():
    """Provides a mock configuration."""
    return {
        'paths': {'stockfish': '/usr/games/stockfish'},
        'experiment': {'engine_skill_level': 1}
    }

def test_game_manager_initialization(mock_dependencies, mock_config):
    """Task 2.6.1: Tests that the GameManager class initializes correctly."""
    llm_handler, db_session = mock_dependencies
    manager = GameManager(config=mock_config, db_session=db_session, llm_handler=llm_handler, persona_name="Test")
    assert manager is not None
    assert manager.board.is_valid()

def test_play_turn_legal_move(mock_dependencies, mock_config):
    """Task 2.6.2: Tests handling of a legal LLM move."""
    llm_handler, db_session = mock_dependencies
    llm_handler.get_response.return_value = ("e7e5", "A simple reply.") # Mock LLM response

    manager = GameManager(config=mock_config, db_session=db_session, llm_handler=llm_handler, persona_name="Test")
    manager.board = chess.Board("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2") # Set a specific board state
    
    manager._play_llm_turn() # Private method call for testing

    # Verify that the move was made on the board
    assert manager.board.peek() == chess.Move.from_uci("e7e5")
    # Verify the database was called to log the move
    from gambit.game_manager import log_move
    log_move.assert_called_with(session=db_session, game_id=1, is_legal=True, move_notation="e7e5", llm_commentary="A simple reply.")

def test_play_turn_illegal_move(mock_dependencies, mock_config):
    """Task 2.6.2: Tests handling of an illegal LLM move."""
    llm_handler, db_session = mock_dependencies
    # Mock the LLM to make an illegal move, then a legal one after confrontation
    llm_handler.get_response.side_effect = [
        ("e1e2", "An illegal move."), # First response is illegal
        ("g1f3", "My apologies, a knight move.") # Second response is legal
    ]

    manager = GameManager(config=mock_config, db_session=db_session, llm_handler=llm_handler, persona_name="Test")
    
    manager._play_llm_turn()

    # Verify the illegal move was logged
    from gambit.game_manager import log_move
    log_move.call_args_list[0].kwargs['is_legal'] == False
    log_move.call_args_list[0].kwargs['move_notation'] == "e1e2"

    # Verify the LLM was called a second time (the confrontation)
    assert llm_handler.get_response.call_count == 2
    # Verify the final, legal move was made
    assert manager.board.peek() == chess.Move.from_uci("g1f3")