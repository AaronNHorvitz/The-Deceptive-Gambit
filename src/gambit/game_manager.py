# src/gambit/game_manager.py

import chess
import chess.engine
from gambit.llm_handler import LLMHandler
from gambit import database
from gambit.move_utils import apply_uci_once, IllegalMoveError, is_move_color_correct


class GameManager:
    def __init__(
        self,
        config: dict,
        db_session,
        persona_name: str,
        target_llm_handler: LLMHandler | None = None,
        persona_llm_handler: LLMHandler | None = None,
        # Back-compat with tests:
        llm_handler: LLMHandler | None = None,
        starting_fen: str | None = None,
        llm_color: chess.Color | None = None,  # not used by tests, but accepted
    ):
        self.config = config
        self.db_session = db_session
        self.persona_name = persona_name

        # Back-compat: if tests pass a single llm_handler, use it for both
        if llm_handler is not None:
            self.target_llm = llm_handler
            self.persona_llm = llm_handler
        else:
            self.target_llm = target_llm_handler
            self.persona_llm = persona_llm_handler
        self.board = chess.Board()
        self.starting_fen = starting_fen or chess.STARTING_FEN
        if starting_fen:
            self.board.set_fen(starting_fen)

        # Track most recent quotes for the end summary
        self.last_llm_comment = ""
        self.last_persona_comment = ""

        # Build a pretty per-move (fullmove) log we’ll print at the end:
        # Each element: {
        #   "no": int,
        #   "white": {"name": str, "san": str, "legal": bool, "quote": str},
        #   "black": {"name": str, "san": str, "legal": bool, "quote": str}
        # }
        self.pretty_fullmoves = []
        
        # Track the most recent commentary lines for the final summary
        self.last_llm_comment = ""          
        self.last_persona_comment = ""      

        self.game_record = database.get_or_create_game(self.db_session, self.persona_name)

        engine_path = self.config['paths']['stockfish']
        self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        skill = self.config['experiment']['engine_skill_level']
        self.engine.configure({"Skill Level": skill})

    def _names(self):
        gpt_name = self.config.get("names", {}).get("gpt", "GPT")
        persona_display = self.config["personas"][self.persona_name].get("display_name", self.persona_name)
        return gpt_name, persona_display

    def _debug(self) -> bool:
        return bool(self.config.get("debug_prints"))


    def play_game(self):
        try:
            while not self.board.is_game_over():
                if self._debug():
                    print(f"[LOOP] start turn={'White' if self.board.turn == chess.WHITE else 'Black'} FEN={self.board.fen()}")
                if self.board.turn == chess.WHITE:
                    if self._debug():
                        print("[LOOP] calling _play_opponent_turn")
                    self._play_opponent_turn()
                else:  # Black's turn (our target LLM)
                    if self._debug():
                        print("[LOOP] calling _play_llm_turn")
                    self._play_llm_turn()
                if self._debug():
                    print("[LOOP] calling _print_game_record")
                #self._print_game_rec
                # ord()
            self._print_final_summary()
        finally:
            try:
                self.engine.quit()
            except chess.engine.EngineTerminatedError:
                pass


    def _play_opponent_turn(self):

        # Stockfish (White) plays
        if self._debug():
            print("[OPP] engine.play(...)")
        result = self.engine.play(self.board, chess.engine.Limit(time=0.1))
        engine_uci = result.move.uci()
        if self._debug():
            print(f"[OPP] engine_uci={engine_uci}")

        # PRE-move FEN for DB (if DB replays/validates it needs White to move)
        fen_before = self.board.fen()
        if self._debug():
            print(f"[OPP] fen_before={fen_before}")

        # SAN from current (pre-push) position
        mv = chess.Move.from_uci(engine_uci)

        if self._debug():
            print(f"[OPP] mv in legal? {mv in self.board.legal_moves}")
        san = self.board.san(mv)
        if self._debug():
            print(f"[OPP] san={san}")

        # Persona reacts to SAN (does not mutate the board)
        commentary = ""
        try:
            prompt = self._build_prompt_for_persona(san)
            _, commentary = self.persona_llm.get_response(prompt)
            self.last_persona_comment = commentary or self.last_persona_comment
        except Exception as e:
            print(f"[WARN] persona_llm failed: {e}")

        # LOG FIRST, against PRE-move FEN, but NEVER let DB kill the turn
        try:
            if self._debug():
                print("[OPP] database.log_move(...) pre-push")
            database.log_move(
                session=self.db_session,
                game_id=self.game_record.id,
                turn_number=self.board.fullmove_number,  # still pre-push
                player="Stockfish",
                move_notation=engine_uci,
                llm_commentary=commentary,
                board_state_fen=fen_before,              # critical: pre-push FEN
            )
            if self._debug():
                print("[OPP] database.log_move ok")
        except Exception as e:
            print(f"[WARN] log_move failed (engine turn): {e}")

        # EXTRA GUARD: ensure engine move matches side-to-move before applying
        if not is_move_color_correct(self.board, engine_uci):
            if self._debug():
                print(f"[GUARD] rejecting wrong-color engine move {engine_uci} at FEN={self.board.fen()}")
            return

        # APPLY ONCE on the live board (this is legal here)
        try:
            if self._debug():
                print("[OPP] apply_uci_once(...)")
            apply_uci_once(self.board, engine_uci)
            if self._debug():
                print(f"[OPP] after push FEN={self.board.fen()}")
        except Exception as e:
            # Even if something bizarre happens, don't crash the game
            print(f"[WARN] failed to apply engine move {engine_uci}: {e}")
            return  # bail this turn; loop continues

        # Print after push
        self._print_turn_summary("Stockfish", engine_uci, commentary)


    def _play_llm_turn(self):
        # Always capture pre-move FEN for logging
        pre_fen = self.board.fen()

        # Ask the LLM for a move
        prompt = self._build_llm_prompt()
        move_uci, commentary = self.target_llm.get_response(prompt)
        self.last_llm_comment = commentary or self.last_llm_comment

        # Print what the LLM *proposed* BEFORE attempting to apply it
        self._print_turn_summary("llm", move_uci, commentary)

        # Try to apply; never let an exception leak out
        is_legal = False
        if move_uci and move_uci != "no_move":
            # --- GUARD: reject if it's the wrong color ---
            if not is_move_color_correct(self.board, move_uci):
                is_legal = False
            else:
                try:
                    apply_uci_once(self.board, move_uci)   # may raise IllegalMoveError
                    is_legal = True
                except Exception:
                    is_legal = False

        # Log attempt #1 (using the pre-move FEN, per tests)
        database.log_move(
            session=self.db_session,
            game_id=self.game_record.id,
            turn_number=self.board.fullmove_number,
            player="llm",
            is_legal=is_legal,
            move_notation=move_uci,
            llm_commentary=commentary,
            board_state_fen=pre_fen,
        )

        if is_legal:
            return

        # Retry once if first was illegal — again, print first, then attempt
        retry_pre_fen = self.board.fen()
        move_uci2, commentary2 = self.target_llm.get_response(self._build_llm_prompt())
        self.last_llm_comment = commentary2 or self.last_llm_comment
        self._print_turn_summary("llm", move_uci2, commentary2)

        is_legal2 = False
        if move_uci2 and move_uci2 != "no_move":
            if not is_move_color_correct(self.board, move_uci2):
                is_legal2 = False
            else:
                try:
                    apply_uci_once(self.board, move_uci2)
                    is_legal2 = True
                except Exception:
                    is_legal2 = False

        database.log_move(
            session=self.db_session,
            game_id=self.game_record.id,
            turn_number=self.board.fullmove_number,
            player="llm",
            is_legal=is_legal2,
            move_notation=move_uci2,
            llm_commentary=commentary2,
            board_state_fen=retry_pre_fen,
        )

        # If both attempts failed, play a fallback move so the game continues
        if not is_legal2:
            # Option A: quick engine assist for Black
            try:
                result = self.engine.play(self.board, chess.engine.Limit(time=0.05))
                fallback_uci = result.move.uci()
                apply_uci_once(self.board, fallback_uci)
                self._print_turn_summary("llm_fallback", fallback_uci, "[fallback: engine]")
                database.log_move(
                    session=self.db_session,
                    game_id=self.game_record.id,
                    turn_number=self.board.fullmove_number,
                    player="llm_fallback",
                    is_legal=True,
                    move_notation=fallback_uci,
                    llm_commentary="[fallback: engine]",
                    board_state_fen=self.board.fen(),
                )
                self.last_llm_comment = "[fallback: engine]"
                return
            
            except Exception as e:
                # Option B: deterministic simple fallback (first legal move)
                try:
                    mv = next(iter(self.board.legal_moves))
                    fallback_uci = mv.uci()
                    apply_uci_once(self.board, fallback_uci)
                    self._print_turn_summary("llm_fallback", fallback_uci, "[fallback: first-legal]")
                    database.log_move(
                        session=self.db_session,
                        game_id=self.game_record.id,
                        turn_number=self.board.fullmove_number,
                        player="llm_fallback",
                        is_legal=True,
                        move_notation=fallback_uci,
                        llm_commentary="[fallback: first-legal]",
                        board_state_fen=self.board.fen(),
                    )
                    self.last_llm_comment = "[fallback: first-legal]"
                    return
                except StopIteration:
                    # No legal moves → the position is actually terminal; let the loop finish.
                    pass

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
        base = chess.Board(self.starting_fen)
        pgn_history = base.variation_san(list(self.board.move_stack))
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
        base = chess.Board(self.starting_fen)
        pgn_history = base.variation_san(list(self.board.move_stack))
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

        # Pretty score table
        self._print_score_table()

        # Final quotes (use last non-empty seen during the game)
        if self.last_llm_comment or self.last_persona_comment:
            print()
            print(f'- GPT says, "{self.last_llm_comment or ""}"')
            print(f'- {self.persona_name} says, "{self.last_persona_comment or ""}"')

    def _moves_rows(self):
        """Return [(move_no, white_san, black_san), ...] from the move stack."""
        base = chess.Board(self.starting_fen)
        moves = list(self.board.move_stack)
        rows = []
        move_no = 1
        i = 0
        while i < len(moves):
            w_san = base.san(moves[i]); base.push(moves[i]); i += 1
            b_san = ""
            if i < len(moves):
                b_san = base.san(moves[i]); base.push(moves[i]); i += 1
            rows.append((move_no, w_san, b_san))
            move_no += 1
        return rows

    def _print_score_table(self):
        """Pretty-prints the game as a Move/White/Black table."""
        rows = self._moves_rows()
        if not rows:
            print("No moves played.")
            return
        print('\nMove\tWhite\tBlack')  # header
        for n, w, b in rows:
            print(f"{n}.\t{w}\t{b}")



