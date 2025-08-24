# src/tests/test_llm_handler.py

import pytest
from unittest.mock import MagicMock, patch

from gambit.llm_handler import LLMHandler

@pytest.fixture
def mock_config():
    """Provides a mock configuration for tests."""
    return {
        'model_paths': {'target_llm': 'mock/model'},
        'inference_params': {'max_tokens': 150}
    }

# Patch the pipeline function from the transformers library
@patch('transformers.pipeline')
def test_llm_handler_parsing(mock_pipeline, mock_config):
    """Tests that the handler correctly initializes and parses the pipeline's output."""
    # This is the fake output we want our mocked pipeline to produce
    mock_output = [
        {"generated_text": [
            {"role": "system", "content": "..."},
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "e7e5, an interesting, if somewhat passive, response."}
        ]}
    ]
    # Configure the mock to return our fake output
    mock_pipeline.return_value = MagicMock(return_value=mock_output)

    # Initialize the handler (this will use the mocked pipeline)
    handler = LLMHandler(config=mock_config)
    assert handler is not None

    # Call the method and check the parsing logic
    move, commentary = handler.get_response(conversation_history=[])
    assert move == "e7e5"
    assert commentary == "an interesting, if somewhat passive, response."