# src/tests/test_llm_handler.py

import pytest
from unittest.mock import MagicMock, patch
from gambit.llm_handler import LLMHandler

@pytest.fixture
def mock_config():
    return {
        'model_paths': {'target_llm': 'mock/model'},
        'inference_params': {'max_tokens': 150}
    }

@patch('gambit.llm_handler.ollama.Client')
def test_llm_handler_parsing(mock_client_cls, mock_config):
    # Fake Ollama client
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.chat.return_value = {
        'message': {'content': "e7e5, an interesting, if somewhat passive, response."}
    }

    handler = LLMHandler(config=mock_config)
    move, commentary = handler.get_response(conversation_history=[])

    assert move == "e7e5"
    assert commentary == "an interesting, if somewhat passive, response."
