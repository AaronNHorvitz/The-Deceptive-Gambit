# src/gambit/llm_handler.py

import ollama

class LLMHandler:
    """
    Handles all communication with a locally running Ollama server.
    """
    def __init__(self, config: dict):
        self.config = config
        self.model_name = config['model_paths']['target_llm']
        self.client = ollama.Client()

    def get_response(self, conversation_history: list) -> tuple[str, str]:
        """
        Gets a response from the Ollama model and parses it.
        """
        params = self.config['inference_params']
        
        response = self.client.chat(
            model=self.model_name,
            messages=conversation_history,
            options={
                'temperature': params.get('temperature', 0.7),
                'top_p': params.get('top_p', 1.0),
                'num_predict': params.get('max_tokens', 150),
            }
        )
        raw_text = response['message']['content']
        
        parts = raw_text.split(',', 1)
        move = parts[0].strip()
        commentary = parts[1].strip() if len(parts) > 1 else ""
        
        return move, commentary