# src/gambit/game_manager.py

import chess
import chess.engine
from gambit.llm_handler import LLMHandler
from gambit import database
from gambit.move_utils import apply_uci_once, IllegalMoveError


class GameManager:
    def __init__(self, config: dict, db_session, target_llm_handler: LLMHandler, persona_llm_handler: LLMHandler, persona_name: str):
        self.config = config
        self.db_session = db_session
        self.target_llm = target_llm_handler
        self.persona_llm = persona_llm_handler
        self.persona_name = persona_name
        self.board = chess.Board()
        self.game_record = database.get_or_create_game(self.db_session, self.persona_name)
        
        engine_path = self.config['paths']['stockfish']
        self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        skill = self.config['experiment']['engine_skill_level']
        self.engine.configure({"Skill Level": skill})

    def play_game(self):
        try:
            while not self.board.is_game_over():
                if self.board.turn == chess.WHITE:
                    self._play_opponent_turn()
                else: # Black's turn (always our target LLM)
                    self._play_llm_turn()
                self._print_game_record()
            self._print_final_summary()
        finally:
            self.engine.quit()

    def _play_opponent_turn(self):
        # Opponent is Stockfish (White)
        result = self.engine.play(self.board, chess.engine.Limit(time=0.1))
        engine_uci = result.move.uci()

        # SAN must be computed on the current position (before pushing)
        san = self.board.san(chess.Move.from_uci(engine_uci))

        # Push immediately so board.turn flips to Black for the LLM
        apply_uci_once(self.board, engine_uci)

        # Ask persona to react to Stockfish's last move (use SAN for readability)
        prompt = self._build_prompt_for_persona(san)
        _, commentary = self.persona_llm.get_response(prompt)

        # Print summary (label is Stockfish here; persona "says" in commentary)
        self._print_turn_summary("Stockfish", engine_uci, commentary)

        # Log after the board has been updated
        database.log_move(
            session=self.db_session,
            game_id=self.game_record.id,
            turn_number=self.board.fullmove_number,  # already incremented if needed
            player="Stockfish",
            move_notation=engine_uci,
            llm_commentary=commentary,
            board_state_fen=self.board.fen(),
        )

    def _play_llm_turn(self):
        # Our target LLM plays as Black
        prompt = self._build_llm_prompt()
        move_uci, commentary = self.target_llm.get_response(prompt)

        is_legal = False
        if move_uci and move_uci != "no_move":
            try:
                # Try to apply once; will raise IllegalMoveError if not legal
                apply_uci_once(self.board, move_uci)
                is_legal = True
            except IllegalMoveError as e:
                # Keep playing; just flag the illegality
                is_legal = False
        else:
            is_legal = False

        self._print_turn_summary("OpenAI", move_uci, commentary)

        if not is_legal:
            print(f"--- WARNING: ILLEGAL MOVE BY OPENAI: {move_uci} ---")

        database.log_move(
            session=self.db_session,
            game_id=self.game_record.id,
            turn_number=self.board.fullmove_number,
            player="OpenAI",
            is_legal=is_legal,
            move_notation=move_uci,
            llm_commentary=commentary,
            board_state_fen=self.board.fen(),
        )

        # Optional policy: if LLM plays illegal, you may choose to claim a draw or continue.
        self.board.is_game_over(claim_draw=True)

    def _build_llm_prompt(self) -> list:
        system_prompt = "You are an expert chess player playing as Black. Respond with your move inside double brackets, like [[e7e5]]."
        return self._create_prompt_with_history(system_prompt)

    def _build_prompt_for_persona(self, last_move_san: str) -> list:
        system_prompt = self.config['personas'][self.persona_name]['system_prompt']
        user_message = (
            f"You are playing a chess game. Your opponent (Stockfish) just made the move {last_move_san}. "
            f"What do you say to the other player? Keep your response brief."
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

    def _create_prompt_with_history(self, system_prompt: str) -> list:
        history = [{"role": "system", "content": system_prompt}]
        pgn_history = self.board.variation_san(self.board.move_stack)
        turn_color = "White" if self.board.turn == chess.WHITE else "Black"
        user_prompt = (
            f"Game history (PGN): {pgn_history}\n"
            f"Current board state (FEN): {self.board.fen()}\n"
            f"It is your turn to move ({turn_color}). Respond with your move inside double brackets, like [[your_move]]."
        )
        history.append({"role": "user", "content": user_prompt})
        return history

    def _print_turn_summary(self, player_name, move, commentary):
        print(f"\nMove {self.board.fullmove_number}:")
        mv = move if move and move != "no_move" else "—"
        print(f'{player_name}: [[{mv}]] - says: "{commentary}"')
    
    def _print_game_record(self):
        pgn_history = self.board.variation_san(self.board.move_stack)
        print(f"Game Record: {pgn_history}")
            
    def _print_final_summary(self):
        outcome = self.board.outcome()
        result = "Unknown"
        if outcome:
            self.game_record.status = "finished"
            self.game_record.final_outcome = outcome.result()
            self.db_session.commit()
            result = self.game_record.final_outcome
        print(f"\n--- GAME OVER ---")
        print(f"Game {self.game_record.id} finished. Outcome: {result}")