# src/gambit/llm_handler.py

import ollama
import re
import concurrent.futures


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
        temperature = params.get('temperature', 0.7)
        # Ollama uses num_predict to cap output tokens
        num_predict = params.get('max_tokens', 150)
        timeout_s = params.get('timeout_s', 10)  # <-- add this to config if you want to tweak

        def _do_chat():
            return self.client.chat(
                model=self.model_name,
                messages=conversation_history,
                options={
                    'temperature': temperature,
                    'num_predict': num_predict,
                }
            )

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(_do_chat)
                response = fut.result(timeout=timeout_s)
        except concurrent.futures.TimeoutError:
            # Hard timeout → no move this turn
            return "no_move", "[timeout]"

        raw_text = response['message']['content']

        match = self.move_regex.search(raw_text)
        if match:
            move = match.group(1) or match.group(2)
            # Remove the first move token from the text
            commentary = self.move_regex.sub('', raw_text, count=1).strip()
            # Strip leading punctuation/whitespace (commas, periods, dashes, etc.)
            commentary = re.sub(r"^[\s,;:.\-–—]+", "", commentary)
        else:
            move = "no_move"
            commentary = raw_text.strip()

        return move, commentary

