# src/gambit/llm_handler.py

# src/gambit/llm_handler.py
import ollama
import re

class LLMHandler:
    def __init__(self, config: dict, model_name: str | None = None):
        self.config = config
        self.model_name = model_name or config.get('model_paths', {}).get('target_llm', 'gpt-oss:20b')
        self.client = ollama.Client()

        # Accept [[e2e4]] OR bare e2e4
        self.move_regex = re.compile(
            r"\[\s*\[([a-h][1-8][a-h][1-8][qrbn]?)\]\s*\]|\b([a-h][1-8][a-h][1-8][qrbn]?)\b"
        )

    def get_response(self, conversation_history: list) -> tuple[str, str]:
        params = self.config.get('inference_params', {})
        response = self.client.chat(
            model=self.model_name,
            messages=conversation_history,
            options={'temperature': params.get('temperature', 0.7)}
        )
        raw_text = response['message']['content']

        match = self.move_regex.search(raw_text)
        if match:
            move = match.group(1) or match.group(2)
            # strip the found token from commentary (and common separators)
            commentary = self.move_regex.sub('', raw_text, count=1).strip()
            # clean leading punctuation/commas/spaces
            commentary = re.sub(r"^[\s,;:.\-–—]+", "", commentary)
        else:
            move = "no_move"
            commentary = raw_text.strip()

        return move, commentary
