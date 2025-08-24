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
        result = self.engine.play(self.board, chess.engine.Limit(time=0.1))
        engine_uci = result.move.uci()

        # PRE-move FEN for DB
        fen_before = self.board.fen()

        # SAN from pre-push position
        mv = chess.Move.from_uci(engine_uci)
        san = self.board.san(mv)

        # DB log first (pre-push FEN)
        try:
            database.log_move(
                session=self.db_session,
                game_id=self.game_record.id,
                turn_number=self.board.fullmove_number,  # still pre-push
                player="Stockfish",
                move_notation=engine_uci,
                llm_commentary="",   # no persona reply here anymore
                board_state_fen=fen_before,
            )
        except Exception as e:
            if self._debug(): print(f"[WARN] log_move failed (engine turn): {e}")

        # Apply once
        apply_uci_once(self.board, engine_uci)

        # Pretty log: start a new fullmove entry (White just played)
        gpt_name, persona_display = self._names()
        self.pretty_fullmoves.append({
            "no": self.board.fullmove_number,   # still this fullmove index (Black to move)
            "white": {"name": persona_display, "san": san, "legal": True, "quote": ""},
            "black": {"name": gpt_name, "san": "", "legal": False, "quote": ""},
        })

        # Print a simple turn summary for White
        self._print_turn_summary(persona_display, engine_uci, "")  # no quote here

    def _play_llm_turn(self):
        gpt_name, persona_display = self._names()
        pre_fen = self.board.fen()

        # Ask GPT for a move
        prompt = self._build_llm_prompt()
        move_uci, gpt_comment = self.target_llm.get_response(prompt)
        self.last_llm_comment = gpt_comment or self.last_llm_comment
        self._print_turn_summary("llm", move_uci, gpt_comment)

        # Try to apply once
        is_legal = False
        chosen_uci = None
        try:
            if move_uci and move_uci != "no_move":
                apply_uci_once(self.board, move_uci)
                chosen_uci = move_uci
                is_legal = True
        except Exception:
            is_legal = False

        # Log attempt #1
        database.log_move(
            session=self.db_session,
            game_id=self.game_record.id,
            turn_number=self.board.fullmove_number,
            player="llm",
            is_legal=is_legal,
            move_notation=move_uci,
            llm_commentary=gpt_comment,
            board_state_fen=pre_fen,
        )

        # Retry if illegal
        if not is_legal:
            retry_pre_fen = self.board.fen()
            move_uci2, gpt_comment2 = self.target_llm.get_response(self._build_llm_prompt())
            self.last_llm_comment = gpt_comment2 or self.last_llm_comment
            self._print_turn_summary("llm", move_uci2, gpt_comment2)

            is_legal2 = False
            try:
                if move_uci2 and move_uci2 != "no_move":
                    apply_uci_once(self.board, move_uci2)
                    chosen_uci = move_uci2
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
                llm_commentary=gpt_comment2,
                board_state_fen=retry_pre_fen,
            )

            is_legal = is_legal2

            # Fallback if still illegal
            if not is_legal:
                try:
                    result = self.engine.play(self.board, chess.engine.Limit(time=0.05))
                    chosen_uci = result.move.uci()
                    apply_uci_once(self.board, chosen_uci)
                    gpt_comment = "[fallback: engine]"
                    self.last_llm_comment = gpt_comment
                    self._print_turn_summary("llm_fallback", chosen_uci, gpt_comment)
                    database.log_move(
                        session=self.db_session,
                        game_id=self.game_record.id,
                        turn_number=self.board.fullmove_number,
                        player="llm_fallback",
                        is_legal=True,
                        move_notation=chosen_uci,
                        llm_commentary=gpt_comment,
                        board_state_fen=self.board.fen(),
                    )
                    is_legal = True
                except Exception:
                    # Try first legal move
                    try:
                        mv = next(iter(self.board.legal_moves))
                        chosen_uci = mv.uci()
                        apply_uci_once(self.board, chosen_uci)
                        gpt_comment = "[fallback: first-legal]"
                        self.last_llm_comment = gpt_comment
                        self._print_turn_summary("llm_fallback", chosen_uci, gpt_comment)
                        database.log_move(
                            session=self.db_session,
                            game_id=self.game_record.id,
                            turn_number=self.board.fullmove_number,
                            player="llm_fallback",
                            is_legal=True,
                            move_notation=chosen_uci,
                            llm_commentary=gpt_comment,
                            board_state_fen=self.board.fen(),
                        )
                        is_legal = True
                    except StopIteration:
                        pass  # terminal

        # If a Black move actually got applied, compute its SAN from pre-fen
        gpt_san = ""
        if chosen_uci:
            base = chess.Board(pre_fen)
            gpt_san = base.san(chess.Move.from_uci(chosen_uci))

        # Persona replies to GPT’s move (short & reactive)
        persona_reply = ""
        if gpt_san:
            try:
                persona_reply_prompt = self._build_persona_reply_to_gpt(gpt_san)
                _, persona_reply = self.persona_llm.get_response(persona_reply_prompt)
                self.last_persona_comment = persona_reply or self.last_persona_comment
            except Exception as e:
                if self._debug(): print(f"[WARN] persona reply failed: {e}")

        # Fill in the current fullmove’s Black slot + quotes
        if self.pretty_fullmoves:
            row = self.pretty_fullmoves[-1]
            row["black"]["name"] = gpt_name
            row["black"]["san"] = gpt_san
            row["black"]["legal"] = bool(chosen_uci)
            row["black"]["quote"] = self.last_llm_comment or ""
            # Attach persona’s reply to the SAME fullmove, on Lily’s line
            if persona_reply:
                row["white"]["quote"] = persona_reply



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
    
    def _print_move_blocks(self):
        gpt_name, persona_display = self._names()
        print(f"\nChess Game {gpt_name} vs. {persona_display}\n")
        for row in self.pretty_fullmoves:
            n = row["no"]
            w = row["white"]; b = row["black"]
            w_legal = "Legal" if w["legal"] else "Illegal"
            b_legal = "Legal" if b["legal"] else "Illegal"
            print(f"Move {n}:")
            print(f'{w["name"]}\t| {w["san"]}\t| {w_legal}\t| "{w["quote"]}"')
            if b["san"] or b["quote"]:
                print(f'{b["name"]}\t| {b["san"]}\t| {b_legal}\t| "{b["quote"]}"')
            print()  # blank line between moves

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

        # Full, human-readable move blocks with quotes
        self._print_move_blocks()

        # Compact table (unchanged)
        self._print_score_table()

        # Final quotes (last-seen fallbacks)
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

    def _build_persona_reply_to_gpt(self, gpt_move_san: str) -> list:
        system_prompt = self.config['personas'][self.persona_name]['system_prompt']
        user_message = (
            f"Your opponent (GPT) just played {gpt_move_san}. "
            f"Reply with a short, in-character reaction."
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
    ]

    def _print_game_record(self):
        pass
