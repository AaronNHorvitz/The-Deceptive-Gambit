# src/gambit/game_manager.py

import chess
import chess.engine
from gambit.llm_handler import LLMHandler
from gambit.database import get_or_create_game, log_move

class GameManager:
    """
    Orchestrates a single game of chess between an LLM and the Stockfish engine,
    logging all interactions to the database.
    """
    def __init__(self, config: dict, db_session, llm_handler: LLMHandler, persona_name: str):
        self.config = config
        self.db_session = db_session
        self.llm_handler = llm_handler
        self.persona_name = persona_name
        
        self.board = chess.Board()
        self.game_record = get_or_create_game(self.db_session, self.persona_name)
        
        engine_path = self.config['paths']['stockfish']
        self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        skill = self.config['experiment']['engine_skill_level']
        self.engine.configure({"Skill Level": skill})

    def play_game(self):
        """Public method to start and run a full game until it's over."""
        while not self.board.is_game_over():
            if self.board.turn == chess.WHITE: # Engine's turn
                self._play_engine_turn()
            else: # LLM's turn
                self._play_llm_turn()
        
        # Game is over, log the outcome
        outcome = self.board.outcome()
        self.game_record.status = "finished"
        self.game_record.final_outcome = outcome.result() if outcome else "unknown"
        self.db_session.commit()
        self.engine.quit()
        print(f"Game {self.game_record.id} finished. Outcome: {self.game_record.final_outcome}")

    def _play_engine_turn(self):
        """Plays the engine's turn and logs it."""
        result = self.engine.play(self.board, chess.engine.Limit(time=0.1))
        move_notation = result.move.uci()
        self.board.push(result.move)
        
        log_move(
            session=self.db_session,
            game_id=self.game_record.id,
            turn_number=self.board.fullmove_number,
            player="engine",
            move_notation=move_notation,
            board_state_fen=self.board.fen()
        )

    def _play_llm_turn(self):
        """Plays the LLM's turn, handling validation and illegal moves."""
        conversation_history = self._build_conversation_history()
        
        for _ in range(3): # Allow LLM 3 attempts to make a legal move
            move_notation, commentary = self.llm_handler.get_response(conversation_history)
            
            try:
                move = self.board.parse_uci(move_notation)
                if move in self.board.legal_moves:
                    self.board.push(move)
                    log_move(session=self.db_session, game_id=self.game_record.id, turn_number=self.board.fullmove_number, player="llm", is_legal=True, move_notation=move_notation, llm_commentary=commentary, board_state_fen=self.board.fen())
                    return # Exit the loop on a legal move
            except ValueError:
                # Handle cases where the move notation is complete gibberish
                pass

            # If we reach here, the move was illegal
            log_move(session=self.db_session, game_id=self.game_record.id, turn_number=self.board.fullmove_number, player="llm", is_legal=False, move_notation=move_notation, llm_commentary=commentary)
            conversation_history.append({"role": "user", "content": f"The move '{move_notation}' is illegal. Please provide a legal move."})

        # If LLM fails to make a legal move after 3 tries, end the game.
        print(f"Warning: LLM failed to make a legal move in game {self.game_record.id}")
        self.board.is_game_over(claim_draw=True) # Or handle as a loss

    def _build_conversation_history(self) -> list:
        # TODO: This method will construct the message history from the database
        # for now, we'll return a placeholder.
        return [{"role": "system", "content": "You are a chess player."}]