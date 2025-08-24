# src/gambit/llm_handler.py

import ollama
import re 

class LLMHandler:
    """
    Handles all communication with a locally running Ollama server.
    """
    def __init__(self, config: dict):
        self.config = config
        self.model_name = config['model_paths']['target_llm']
        self.client = ollama.Client()
        # <-- 2. Define the regex pattern here in the constructor.
        # This regex finds a UCI chess move (e.g., e2e4, g1f3, a7a8q).
        self.move_regex = re.compile(r"\b[a-h][1-8][a-h][1-8][qrbn]?\b")

    def get_response(self, conversation_history: list) -> tuple[str, str]:
        """
        Gets a response from the Ollama model and parses it using regex.
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
        print(f"[LLM RAW RESPONSE]: {raw_text}") # Debug print statement
        
        match = self.move_regex.search(raw_text)
        
        if match:
            move = match.group(0)
            # Commentary is everything else in the string
            commentary = self.move_regex.sub('', raw_text).strip(" ,.")
        else:
            # If no move is found, return the whole text as a failed move
            move = raw_text.strip()
            commentary = ""
        
        return move, commentary