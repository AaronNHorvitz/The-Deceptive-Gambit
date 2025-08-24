import chess
import chess.engine
from gambit.llm_handler import LLMHandler
from gambit import database
import time

class GameManager:
    def __init__(self, config: dict, db_session, llm_handler: LLMHandler, persona_name: str):
        self.config = config
        self.db_session = db_session
        self.llm_handler = llm_handler # <-- THIS IS THE CORRECTED LINE
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
                if self.board.turn == chess.WHITE: # Stockfish's turn
                    self._play_engine_turn()
                else: # Target LLM's turn
                    self._play_llm_turn()
            self._print_final_summary()
        finally:
            self.engine.quit()

    def _play_engine_turn(self):
        result = self.engine.play(self.board, chess.engine.Limit(time=0.1))
        self._print_turn_summary("Stockfish", result.move.uci(), "...")
        database.log_move(
            session=self.db_session, game_id=self.game_record.id, turn_number=self.board.fullmove_number,
            player="Stockfish", move_notation=result.move.uci(), board_state_fen=self.board.fen()
        )
        self.board.push(result.move)
        self._print_game_record()

    def _play_llm_turn(self):
        prompt = self._build_llm_prompt()
        move_notation, commentary = self.llm_handler.get_response(prompt)
        
        pre_move_fen = self.board.fen()
        is_legal = False
        try:
            self.board.push_uci(move_notation)
            is_legal = True
        except ValueError:
            is_legal = False
        
        self._print_turn_summary("OpenAI", move_notation, commentary, is_legal)
        
        database.log_move(
            session=self.db_session, game_id=self.game_record.id, turn_number=self.board.fullmove_number,
            player="OpenAI", is_legal=is_legal, move_notation=move_notation, llm_commentary=commentary,
            board_state_fen=pre_move_fen
        )
        if not is_legal:
            print(f"--- WARNING: ILLEGAL MOVE BY OPENAI: {move_notation} ---")
            self.board.is_game_over(claim_draw=True) 

    def _build_llm_prompt(self) -> list:
        system_prompt = self.config['personas'][self.persona_name]['system_prompt']
        history = [{"role": "system", "content": system_prompt}]
        pgn_history = self.board.variation_san(self.board.move_stack)
        
        user_prompt = (f"Game history (PGN): {pgn_history}\n"
                       f"The current board state is: {self.board.fen()}\n"
                       f"It is your turn (Black). Respond with your move inside double brackets, like [[e7e5]].")
        history.append({"role": "user", "content": user_prompt})
        return history
            
    def _print_game_record(self):
        pgn_history = self.board.variation_san(self.board.move_stack)
        print(f"Game Record: {pgn_history}")

    def _print_turn_summary(self, player_name, move, commentary, is_legal=True):
        print(f"\nMove {self.board.fullmove_number}:")
        print(f'{player_name}: [[{move}]] - says: "{commentary}"')
    
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