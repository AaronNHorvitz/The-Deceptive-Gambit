# src/gambit/llm_handler.py

import torch
from transformers import pipeline

class LLMHandler:
    """
    Handles loading and running a model locally using Hugging Face Transformers.
    """
    def __init__(self, config: dict):
        self.config = config
        self.model_path = config['model_paths']['target_llm']
        self.pipe = pipeline(
            "text-generation",
            model=self.model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )

    def get_response(self, conversation_history: list) -> tuple[str, str]:
        """
        Gets a response from the LLM and parses it into a move and commentary.
        """
        params = self.config['inference_params']
        
        outputs = self.pipe(
            conversation_history,
            max_new_tokens=params.get('max_tokens', 150),
            # Note: Other params like temp/top_p might need to be passed differently
            # depending on the pipeline version. We'll start simple.
        )
        # The pipeline returns the full conversation. The last message is the new one.
        raw_text = outputs[0]["generated_text"][-1]['content']
        
        parts = raw_text.split(',', 1)
        move = parts[0].strip()
        commentary = parts[1].strip() if len(parts) > 1 else ""
        
        return move, commentary