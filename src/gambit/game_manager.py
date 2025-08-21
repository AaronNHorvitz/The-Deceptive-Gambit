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
        # This is the main loop for a full game.
        # It will be called by main.py.
        pass # We will implement the full loop later.

    def _play_engine_turn(self):
        # We will implement this later.
        pass

    def _play_llm_turn(self):
        """Plays the LLM's turn, handling validation and illegal moves."""
        conversation_history = self._build_conversation_history()
        
        for _ in range(3): # Allow LLM 3 attempts
            move_notation, commentary = self.llm_handler.get_response(conversation_history)
            
            is_move_legal = False
            move = None
            
            try:
                # First, try to parse the move. This catches malformed strings.
                move = self.board.parse_uci(move_notation)
                # If parsing succeeds, check if it's a legal move.
                if move in self.board.legal_moves:
                    is_move_legal = True
            except (ValueError, chess.InvalidMoveError):
                # If parsing fails, it's definitely not legal.
                is_move_legal = False

            if is_move_legal:
                # --- LEGAL MOVE PATH ---
                pre_move_fen = self.board.fen()
                self.board.push(move)
                log_move(
                    session=self.db_session,
                    game_id=self.game_record.id,
                    turn_number=self.board.fullmove_number,
                    player="llm",
                    is_legal=True,
                    move_notation=move_notation,
                    llm_commentary=commentary,
                    board_state_fen=pre_move_fen # Log the state BEFORE the move
                )
                return # Exit the loop and method on a legal move
            else:
                # --- ILLEGAL MOVE PATH ---
                log_move(
                    session=self.db_session,
                    game_id=self.game_record.id,
                    turn_number=self.board.fullmove_number,
                    player="llm",
                    is_legal=False,
                    move_notation=move_notation,
                    llm_commentary=commentary,
                    board_state_fen=self.board.fen()
                )
                conversation_history.append({"role": "user", "content": f"The move '{move_notation}' is illegal. Please provide a legal move."})
        
        print(f"Warning: LLM failed to make a legal move in game {self.game_record.id}")
        self.board.is_game_over(claim_draw=True)

    def _build_conversation_history(self) -> list:
        # TODO: This method will construct the message history from the database
        return [{"role": "system", "content": "You are a chess player playing Black. Respond with your move in UCI notation, followed by a comma, followed by your commentary. For example: e7e5, A simple reply."}]