# src/gambit/llm_handler.py

import ollama
import re

class LLMHandler:
    def __init__(self, config: dict, model_name: str):
        self.config = config
        self.model_name = model_name
        self.client = ollama.Client()
        self.move_regex = re.compile(r"\[\s*\[([a-h][1-8][a-h][1-8][qrbn]?)\]\s*\]")

    def get_response(self, conversation_history: list) -> tuple[str, str]:
        params = self.config['inference_params']
        response = self.client.chat(
            model=self.model_name,
            messages=conversation_history,
            options={'temperature': params.get('temperature', 0.7)}
        )
        raw_text = response['message']['content']
        
        match = self.move_regex.search(raw_text)
        if match:
            move = match.group(1)
            commentary = self.move_regex.sub('', raw_text).strip()
        else:
            move = "no_move"
            commentary = raw_text.strip()
        
        return move, commentary