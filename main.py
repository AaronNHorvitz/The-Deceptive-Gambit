import argparse
import yaml
from pathlib import Path
import chess
import traceback

from gambit import database
from gambit.llm_handler import LLMHandler
from gambit.game_manager import GameManager

def load_config(config_path="config.yaml"):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description="Run The Deceptive Gambit chess experiment.")
    parser.add_argument('--num-games', type=int, default=1)
    parser.add_argument('--persona', type=str, required=True, help="Must be a persona name from config.yaml")
    args = parser.parse_args()

    config = load_config()
    db_path = Path(config['paths']['database'])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    Session = database.init_db(db_path)
    
    print("--- Initializing LLM Handlers ---")
    target_llm_handler = LLMHandler(config=config, model_name=config['model_paths']['target_llm'])
    persona_llm_handler = LLMHandler(config=config, model_name=config['model_paths']['persona_llm'])
    print("Handlers initialized.")

    print(f"\n--- Running Persona: {args.persona} for {args.num_games} game(s) ---")
    for i in range(args.num_games):
        print(f"\n--- Starting Game {i + 1} of {args.num_games} ---")
        db_session = Session()
        try:
            game_manager = GameManager(
                config=config,
                db_session=db_session,
                target_llm_handler=target_llm_handler,
                persona_llm_handler=persona_llm_handler,
                persona_name=args.persona,
            )
            game_manager.play_game()
        except Exception as e:
            print(f"\n--- An error occurred during game {i + 1}: {e} ---")
            traceback.print_exc() 
        finally:
            db_session.close()
    
    print("\n--- Experiment Finished ---")

if __name__ == "__main__":
    main()