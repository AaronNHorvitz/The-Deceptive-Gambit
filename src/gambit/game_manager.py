# src/gambit/game_manager.py

import chess
import chess.engine
from gambit.llm_handler import LLMHandler
from gambit import database

class GameManager:
    def __init__(self, config: dict, db_session, llm_handler: LLMHandler, persona_name: str, starting_fen: str = None):
        self.config = config
        self.db_session = db_session
        self.llm_handler = llm_handler
        self.persona_name = persona_name
        self.llm_color = chess.BLACK # Assuming LLM is always Black for now
        
        if starting_fen:
            self.board = chess.Board(starting_fen)
        else:
            self.board = chess.Board()
        
        self.game_record = database.get_or_create_game(self.db_session, self.persona_name)
        self.conversation_history = self._build_initial_history()
        
        engine_path = self.config['paths']['stockfish']
        self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        skill = self.config['experiment']['engine_skill_level']
        self.engine.configure({"Skill Level": skill})

    def play_game(self):
        try:
            while not self.board.is_game_over():
                if self.board.turn == self.llm_color:
                    self._play_llm_turn()
                else:
                    self._play_engine_turn()
            
            outcome = self.board.outcome()
            if outcome:
                self.game_record.status = "finished"
                self.game_record.final_outcome = outcome.result()
                self.db_session.commit()
            print(f"Game {self.game_record.id} finished. Outcome: {self.game_record.final_outcome}")
        finally:
            self.engine.quit()

    def _play_engine_turn(self):
        result = self.engine.play(self.board, chess.engine.Limit(time=0.1))
        move_notation = result.move.uci()
        self.board.push(result.move)
        
        # Add engine's move to the conversation history for the LLM
        self.conversation_history.append({"role": "user", "content": move_notation})

        database.log_move(
            session=self.db_session, game_id=self.game_record.id, turn_number=self.board.fullmove_number,
            player="engine", move_notation=move_notation, board_state_fen=self.board.fen()
        )

    def _play_llm_turn(self):
        for _ in range(3):
            move_notation, commentary = self.llm_handler.get_response(self.conversation_history)
            pre_move_fen = self.board.fen()
            try:
                self.board.push_uci(move_notation)
                self.conversation_history.append({"role": "assistant", "content": f"{move_notation}, {commentary}"})
                database.log_move(
                    session=self.db_session, game_id=self.game_record.id, turn_number=self.board.fullmove_number,
                    player="llm", is_legal=True, move_notation=move_notation, llm_commentary=commentary,
                    board_state_fen=pre_move_fen
                )
                return
            except ValueError:
                database.log_move(
                    session=self.db_session, game_id=self.game_record.id, turn_number=self.board.fullmove_number,
                    player="llm", is_legal=False, move_notation=move_notation, llm_commentary=commentary,
                    board_state_fen=pre_move_fen
                )
                self.conversation_history.append({"role": "user", "content": f"The move '{move_notation}' is illegal. Please provide a legal move."})
        
        print(f"Warning: LLM failed to make a legal move in game {self.game_record.id}")
        self.board.is_game_over(claim_draw=True)

    def _build_initial_history(self) -> list:
        system_prompt = self.config['personas'][self.persona_name]['system_prompt']
        # For simplicity, we assume the game starts from the beginning for now
        return [{"role": "system", "content": system_prompt}]