# src/tests/tests_llm_handler.py

import pytest
from unittest.mock import MagicMock

# Import the code we are ABOUT to write
from gambit.llm_handler import LLMHandler

@pytest.fixture
def mock_config():
    """Provides a mock configuration for tests."""
    return {
        'model_paths': {
            'target_llm': 'mock/model',
        },
        'inference_params': {
            'temperature': 0.7,
            'top_p': 0.95,
            'max_tokens': 150,
        }
    }

def test_llm_handler_initialization(mock_config):
    """Task 2.4.1: Tests that the LLMHandler class can be initialized."""
    handler = LLMHandler(config=mock_config)
    assert handler is not None
    assert handler.client.base_url == "http://localhost:8000/v1"

def test_get_response_parsing(mock_config, monkeypatch):
    """Task 2.4.2: Tests that the handler correctly parses the LLM's output."""
    # Create a fake response object that the mocked client will return
    mock_response = MagicMock()
    # This is the raw string we imagine the LLM will output
    mock_response.choices[0].message.content = "e7e5, an interesting, if somewhat passive, response."
    
    # Create a mock client that returns our fake response
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    # Use pytest's monkeypatch to replace the real OpenAI client with our mock
    monkeypatch.setattr("openai.OpenAI", lambda base_url, api_key: mock_client)

    # Now, initialize the handler and call the method
    handler = LLMHandler(config=mock_config)
    move, commentary = handler.get_response(conversation_history=[])

    # Assert that our parsing logic worked correctly
    assert move == "e7e5"
    assert commentary == "an interesting, if somewhat passive, response."