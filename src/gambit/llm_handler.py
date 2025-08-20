# src/gambit/llm_handler.py

import openai

class LLMHandler:
    """
    Handles all communication with a vLLM-served, OpenAI-compatible API.
    """
    def __init__(self, config: dict, base_url: str = "http://localhost:8000/v1"):
        self.config = config
        self.model_name = config['model_paths']['target_llm']
        self.client = openai.OpenAI(
            base_url=base_url,
            api_key="EMPTY" # vLLM server does not require an API key
        )

    def get_response(self, conversation_history: list) -> tuple[str, str]:
        """
        Gets a response from the LLM and parses it into a move and commentary.

        Args:
            conversation_history: A list of messages in OpenAI format.

        Returns:
            A tuple containing the move notation (str) and the commentary (str).
        """
        params = self.config['inference_params']
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=conversation_history,
            temperature=params.get('temperature', 0.7),
            top_p=params.get('top_p', 1.0),
            max_tokens=params.get('max_tokens', 150),
        )

        raw_text = response.choices[0].message.content
        
        # Simple parsing logic: assume the move is the first "word"
        # separated by a comma from the rest of the commentary.
        parts = raw_text.split(',', 1)
        move = parts[0].strip()
        commentary = parts[1].strip() if len(parts) > 1 else ""
        
        return move, commentary