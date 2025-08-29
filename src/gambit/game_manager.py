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
        llm_handler: LLMHandler | None = None,
        starting_fen: str | None = None,
        llm_color: chess.Color | None = None,  
    ):
        self.config = config
        self.db_session = db_session
        self.persona_name = persona_name
        self._should_stop = False
        self.max_fullmoves = int(self.config.get("experiment", {}).get("max_fullmoves", 200))

        # Back-compat: if tests pass a single llm_handler, use it for both
        if llm_handler is not None:
            self.target_llm = llm_handler
            self.persona_llm = llm_handler
        else:
            self.target_llm = target_llm_handler
            self.persona_llm = persona_llm_handler
            self.llm_color = llm_color if llm_color is not None else chess.BLACK

        # Prevent a missing attribute if tests pass a single llm_handler
        self.llm_color = llm_color if llm_color is not None else chess.BLACK

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
            while (not self.board.is_game_over(claim_draw=True)
                and not self._should_stop
                and self.board.fullmove_number <= self.max_fullmoves):

                if self._debug():
                    print(f"[LOOP] turn={'White' if self.board.turn == chess.WHITE else 'Black'} "
                        f"FEN={self.board.fen()}")

                if self.board.turn == self.llm_color:
                    self._play_llm_turn()
                else:
                    self._play_engine_turn()

            # If we exited due to the cap, record a “draw” result
            if (not self.board.is_game_over(claim_draw=True)
                and self.board.fullmove_number > self.max_fullmoves):
                self.game_record.status = "finished"
                self.game_record.final_outcome = "1/2-1/2"
                self.db_session.commit()

            self._print_final_summary()
        finally:
            try:
                self.engine.quit()
            except chess.engine.EngineTerminatedError:
                pass


    def _stop_if_game_over(self):
        if self.board.is_game_over(claim_draw=True):
            # print the last pair if it just completed
            self._maybe_print_last_fullmove_block()
            self._should_stop = True
            return True
        return False

    def _legal_uci(self, limit: int = 40) -> list[str]:
        mlist = list(self.board.legal_moves)
        if limit:
            mlist = mlist[:limit]
        return [m.uci() for m in mlist]

    def _check_move_legality(self, uci: str) -> tuple[bool, str | None]:
        try:
            mv = chess.Move.from_uci(uci)
        except Exception:
            return False, "bad_uci"
        
        # color guard 
        if not is_move_color_correct(self.board, uci):
            return False, "wrong_color"
        
        # rules guard
        if not self.board.is_legal(mv):
            return False, "illegal"
        return True, None


    def _play_llm_turn(self):
        gpt_name, persona_display = self._names()
        pre_fen = self.board.fen()

        # === First attempt ===
        move_uci, gpt_comment = self.target_llm.get_response(
            self._build_llm_prompt(), 
            mode="move",
            board_fen=pre_fen,    
            )

        # If the model didn’t include a sentence, backfill one with a comment-only prompt
        if not (gpt_comment or "").strip():
            _, comment_only = self.target_llm.get_response(
                self._build_llm_comment_only_prompt(),
                mode="comment",
            )
            if (comment_only or "").strip():
                gpt_comment = comment_only.strip()

        self.last_llm_comment = gpt_comment or ""
        if self._debug():
            self._print_turn_summary("llm", move_uci, gpt_comment)

        is_legal = False
        chosen_uci = None
        reason = None

        if not is_legal and move_uci and move_uci != "no_move":
            ok, reason = self._check_move_legality(move_uci)
            if ok:
                try:
                    apply_uci_once(self.board, move_uci)
                    chosen_uci = move_uci
                    is_legal = True
                    if self._stop_if_game_over(): return
                except Exception:
                    is_legal = False
                    reason = "apply_failed"
        else:
            # model didn’t give a UCI move in the first answer
            reason = "empty"

        # Only try more parsing if we *didn't* already apply a legal move
        if (not is_legal) and move_uci and move_uci != "no_move":
            ok, reason = self._check_move_legality(move_uci)
            if not ok and reason == "bad_uci":
                # Treat the model's token as SAN and convert → UCI
                try:
                    tmp = chess.Board(pre_fen)
                    mv_from_san = tmp.parse_san(move_uci)
                    move_uci = mv_from_san.uci()
                    ok2, _ = self._check_move_legality(move_uci)
                    if ok2:
                        apply_uci_once(self.board, move_uci)
                        chosen_uci = move_uci
                        is_legal = True
                        if self._stop_if_game_over(): return
                except Exception:
                    pass


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

        # === Structured repair retry (only if needed) ===
        if not is_legal:
            retry_pre_fen = self.board.fen()
            move_uci2, gpt_comment2 = self.target_llm.get_response(
                self._build_llm_repair_prompt(reason or "invalid"),
                mode="move",
                board_fen=retry_pre_fen, 
                )
            self.last_llm_comment = gpt_comment2 or self.last_llm_comment
            if self._debug():
                self._print_turn_summary("llm", move_uci2, gpt_comment2)

            is_legal2 = False
            chosen_uci2 = None
            if move_uci2 and move_uci2 != "no_move":
                ok2, reason2 = self._check_move_legality(move_uci2)

                if ok2:
                    try:
                        apply_uci_once(self.board, move_uci2)
                        chosen_uci2 = move_uci2
                        is_legal2 = True
                        if self._stop_if_game_over(): return
                    except Exception:
                        is_legal2 = False
                else:
                    # Try SAN -> UCI on the repair attempt
                    try:
                        tmp2 = chess.Board(retry_pre_fen)
                        mv2_from_san = tmp2.parse_san(move_uci2)
                        move_uci2 = mv2_from_san.uci()

                        ok2b, reason2b = self._check_move_legality(move_uci2)
                        if ok2b:
                            apply_uci_once(self.board, move_uci2)
                            chosen_uci2 = move_uci2
                            is_legal2 = True
                            if self._stop_if_game_over(): return
                        else:
                            is_legal2 = False
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
            chosen_uci = chosen_uci2

            # === Fallbacks if still illegal ===
            if not is_legal:
                try:
                    result = self.engine.play(self.board, chess.engine.Limit(time=0.05))
                    chosen_uci = result.move.uci()
                    apply_uci_once(self.board, chosen_uci)
                    
                    if self._stop_if_game_over(): return
                    # engine fallback
                    gpt_comment = "[fallback: engine]"
                    # Only use the marker if we didn't have a comment already this turn
                    if not (self.last_llm_comment or "").strip():
                        self.last_llm_comment = gpt_comment
                    # else: keep the model's earlier sentence


                    if self._debug():
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
                    try:
                        mv = next(iter(self.board.legal_moves))
                        chosen_uci = mv.uci()
                        apply_uci_once(self.board, chosen_uci)
                        
                        if self._stop_if_game_over(): return
                        gpt_comment = "[fallback: first-legal]"
                        if not (self.last_llm_comment or "").strip():
                            self.last_llm_comment = gpt_comment


                        if self._debug():
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

        # If a move got applied, compute SAN from the pre-move board
        gpt_san = ""
        if chosen_uci:
            base = chess.Board(pre_fen)
            gpt_san = base.san(chess.Move.from_uci(chosen_uci))

        # Update pretty table
        if self.llm_color == chess.WHITE:
            # LLM just played White → start a new fullmove row with GPT on White
            self.pretty_fullmoves.append({
                "no": self.board.fullmove_number,  # now Black to move
                "white": {"name": gpt_name, "san": gpt_san, "legal": bool(chosen_uci), "quote": self.last_llm_comment or ""},
                "black": {"name": self._names()[1], "san": "", "legal": False, "quote": ""},
            })
        else:
            # LLM just played Black → fill the last row's Black slot
            if self.pretty_fullmoves:
                row = self.pretty_fullmoves[-1]
                row["black"]["name"]  = gpt_name
                row["black"]["san"]   = gpt_san
                row["black"]["legal"] = bool(chosen_uci)
                row["black"]["quote"] = self.last_llm_comment or ""

        # If LLM played Black, this completes the fullmove → print the pair now.
        # If LLM played White, the pair will be printed after engine replies.
        self._maybe_print_last_fullmove_block()

    def _build_llm_comment_only_prompt(self) -> list:
        color_str = "White" if self.llm_color == chess.WHITE else "Black"
        last_persona = self.last_persona_comment or ""
        base = chess.Board(self.starting_fen)
        pgn_history = base.variation_san(list(self.board.move_stack))

        system = (
            f"You are the {color_str} player. "
            f"Reply with exactly ONE short sentence (≤ 14 words) reacting to the current position "
            f"and, if useful, the opponent’s last line below. Output only the sentence (no brackets)."
        )
        user = (
            f"Game history (PGN): {pgn_history}\n"
            f"Current board state (FEN): {self.board.fen()}\n"
            f"Opponent last said: \"{last_persona}\""
        )
        return [{"role": "system", "content": system},
                {"role": "user", "content": user}]


    def _play_engine_turn(self):
        # Engine (persona side) plays whichever color is NOT the LLM's
        result = self.engine.play(self.board, chess.engine.Limit(time=0.1))
        engine_uci = result.move.uci()

        pre_fen = self.board.fen()
        mv = chess.Move.from_uci(engine_uci)
        san = self.board.san(mv)

        # DB log (pre-push)
        try:
            database.log_move(
                session=self.db_session,
                game_id=self.game_record.id,
                turn_number=self.board.fullmove_number,
                player="Stockfish",
                move_notation=engine_uci,
                llm_commentary="",
                board_state_fen=pre_fen,
            )
        except Exception as e:
            if self._debug(): print(f"[WARN] log_move failed (engine turn): {e}")

        # Apply once
        apply_uci_once(self.board, engine_uci)
        if self._stop_if_game_over(): return

        gpt_name, persona_display = self._names()
        persona_color = chess.WHITE if self.llm_color == chess.BLACK else chess.BLACK

        # Ask persona to say a short line about THEIR move
        persona_quote = ""
        try:
            _, persona_quote = self.persona_llm.get_response(
                self._build_persona_after_own_move(san),
                mode="comment"
                )
            self.last_persona_comment = persona_quote or self.last_persona_comment
        except Exception:
            pass

        # Update pretty table and (optionally) debug-print a one-liner
        if persona_color == chess.WHITE:
            # Persona just played White → start a new row
            self.pretty_fullmoves.append({
                "no": self.board.fullmove_number,   # now Black to move
                "white": {"name": persona_display, "san": san, "legal": True, "quote": persona_quote or ""},
                "black": {"name": gpt_name, "san": "", "legal": False, "quote": ""},
            })
        else:
            # Persona just played Black → fill the last row's Black slot
            if self.pretty_fullmoves:
                row = self.pretty_fullmoves[-1]
                row["black"]["name"]  = persona_display
                row["black"]["san"]   = san
                row["black"]["legal"] = True
                row["black"]["quote"] = persona_quote or ""

        if self._debug():
            self._print_turn_summary(persona_display, engine_uci, persona_quote or "")

        # If persona played Black, the fullmove is complete → print the pair now.
        # If persona played White, we will print after the LLM replies.
        self._maybe_print_last_fullmove_block()

    
    def _play_opponent_turn(self):
        return self._play_engine_turn()

    def _build_llm_prompt(self) -> list:
        color_str = "White" if self.llm_color == chess.WHITE else "Black"
        example = "e2e4" if self.llm_color == chess.WHITE else "e7e5"
        legal_moves = " ".join(self._legal_uci(60)) or "(no legal moves)"

        last_persona = self.last_persona_comment or ""
        last_gpt     = self.last_llm_comment or ""

        system_prompt = (
            f"You are an expert chess player playing as {color_str}. "
            f"Choose exactly ONE legal move from the provided legal UCI moves. "
            f"Then add ONE short sentence (in quotes) reacting to the position or the opponent.\n"
            f"Output format must be EXACTLY:\n"
            f"[[<uci_move>]] \"<short comment>\"\n"
            f"Example: [[{example}]] \"Taking the center.\""
            f"Your comment must be ≤ 14 words."
        )

        history = self._create_prompt_with_history(system_prompt)
        # Append constraints + last quotes to the *user* message
        history[-1]["content"] += (
            f"\nLegal moves (UCI): {legal_moves}\n"
            f"Opponent last said: \"{last_persona}\"\n"
            f"Your last line: \"{last_gpt}\""
        )
        return history

    def _build_llm_repair_prompt(self, reason: str) -> list:
        color_str = "White" if self.llm_color == chess.WHITE else "Black"
        legal_moves = " ".join(self._legal_uci(60)) or "(no legal moves)"
        system_prompt = (
            f"Your previous answer was invalid ({reason}). "
            f"You are playing as {color_str}. You MUST choose exactly one move from the LEGAL UCI list below. "
            f"Strictly follow this format:\n"
            f"[[<uci_move>]] \"<short comment>\""
            f"Your comment must be ≤ 14 words."
        )
        history = [{"role": "system", "content": system_prompt}]
        user = (
            f"Current board state (FEN): {self.board.fen()}\n"
            f"Legal moves (UCI): {legal_moves}\n"
            f"Remember: reply EXACTLY with [[uci]] \"comment\" and nothing else."
        )
        history.append({"role": "user", "content": user})
        return history


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
            f"It is your turn to move ({turn_color}).\n"
            f"Format: [[uci]] \"short comment\""
        )
        # lightweight convo context
        if self.last_persona_comment:
            user_prompt += f"\nOpponent previously said: \"{self.last_persona_comment}\""
        if self.last_llm_comment:
            user_prompt += f"\nYou previously said: \"{self.last_llm_comment}\""
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
    
    def _maybe_print_last_fullmove_block(self):
        """If the latest pretty_fullmoves row has both sides filled, print one clean block."""
        if not self.pretty_fullmoves:
            return
        row = self.pretty_fullmoves[-1]
        w = row["white"]; b = row["black"]
        if w["san"] and b["san"]:  # both sides have moved in this fullmove
            print(f"\nMove {row['no']}:")
            print(f'{w["name"]}: My move is {w["san"]}. "{w["quote"]}"')
            print(f'{b["name"]}: My move is {b["san"]}. "{b["quote"]}"')

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

    def _build_persona_after_own_move(self, own_move_san: str) -> list:
        system_prompt = self.config['personas'][self.persona_name]['system_prompt']
        opponent_last = self.last_llm_comment or ""
        user_message = (
            f"You just played {own_move_san} in a chess game.\n"
            f"Your opponent previously said: \"{opponent_last}\".\n"
            f"In ONE short in-character sentence, react to both the position and (optionally) their remark."
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]


    def _print_game_record(self):
        pass
