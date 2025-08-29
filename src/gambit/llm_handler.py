# src/gambit/llm_handler.py

import ollama
import re
import concurrent.futures
import chess

class LLMHandler:

    def __init__(self, config: dict, model_name: str | None = None):
        self.config = config
        self.model_name = model_name or config.get('model_paths', {}).get('target_llm', 'gpt-oss:20b')
        self.client = ollama.Client()

        # 1) [[uci]] "optional comment"
        self.move_and_comment = re.compile(
            r"\[\[\s*([a-h][1-8][a-h][1-8](?:[qrbn])?)\s*\]\]\s*(?:\"([^\"]*)\")?",
            re.IGNORECASE
        )
        # 2) bare uci anywhere in the text
        self.uci_only = re.compile(
            r"\b([a-h][1-8][a-h][1-8](?:[qrbn])?)\b",
            re.IGNORECASE
        )
        # 3) first quoted string (to pull a comment if not right after the move)
        self.first_quote = re.compile(r"\"([^\"]*)\"")

        # Accept both letter-O and zero in castling, and normal SAN (incl. promotions/check)
        castle = r"(?:O-O-O|O-O|0-0-0|0-0)"
        self.san_token = re.compile(
            rf"\b(?:{castle}|[KQRBN]?[a-h]?[1-8]?x?[a-h][1-8](?:=[QRBN])?(?:\+|#)?)\b",
            re.IGNORECASE
        )

    def get_response(self, conversation_history: list, *, mode: str = "auto") -> tuple[str, str]:
        params = self.config.get('inference_params', {})
        temperature = params.get('temperature', 0.7)
        num_predict = params.get('max_tokens', 150)
        timeout_s = params.get('timeout_s', 10)

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
            return "no_move", "[timeout]"

        raw_text = (response.get('message', {}) or {}).get('content', '') or ''
        txt = raw_text.strip()

        # === If caller only wants commentary, don't try to parse a move at all
        if mode.lower() == "comment":

            # Prefer a quoted line if present; else the whole text.
            q = self.first_quote.search(txt)
            comment = (q.group(1).strip() if q else txt)
            # Light cleanup / gentle cap (keeps within your prompt guidance)
            words = comment.split()
            if len(words) > 24:
                comment = " ".join(words[:24])
            return "no_move", comment

        # === 1) [[uci]] "comment"
        m = self.move_and_comment.search(txt)
        if m:
            uci = (m.group(1) or "").lower()
            comment = (m.group(2) or "").strip()
            if not comment:
                start, end = m.span()
                leftover = (txt[:start] + " " + txt[end:]).strip()
                q = self.first_quote.search(leftover)
                comment = (q.group(1).strip() if q else leftover.lstrip(" .,:;—–-"))
            words = comment.split()
            if len(words) > 14:
                comment = " ".join(words[:14])
            return uci, comment

        # === 2) bare UCI anywhere
        m2 = self.uci_only.search(txt)
        if m2:
            uci = (m2.group(1) or "").lower()
            before = txt[:m2.start()]; after = txt[m2.end():]
            leftover = (before + " " + after).strip()
            q = self.first_quote.search(leftover)
            comment = (q.group(1).strip() if q else leftover.lstrip(" .,:;—–-"))
            words = comment.split()
            if len(words) > 14:
                comment = " ".join(words[:14])
            return uci, comment

        # === 3) SAN fallback (e.g., e4, Nf3, Bxe5+, O-O, 0-0)
        m3 = self.san_token.search(txt)
        if m3:
            san = (m3.group(0) or "").strip()

            # normalize zeros -> letter O so python-chess parses castling
            san_norm = san.replace("0", "O")

            before = txt[:m3.start()]; after = txt[m3.end():]
            leftover = (before + " " + after).strip()
            q = self.first_quote.search(leftover)
            comment = (q.group(1).strip() if q else leftover.lstrip(" .,:;—–-"))

            words = comment.split()
            if len(words) > 14:
                comment = " ".join(words[:14])

            if board_fen:
                try:
                    tmp = chess.Board(board_fen)
                    mv = tmp.parse_san(san_norm)
                    return mv.uci(), comment
                except Exception:
                    pass  # fall through

            return san_norm, comment


