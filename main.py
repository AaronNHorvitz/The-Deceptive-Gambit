import argparse
import yaml
from pathlib import Path

# Import our project modules
from gambit import database
from gambit.llm_handler import LLMHandler
from gambit.game_manager import GameManager

def load_config(config_path="config.yaml"):
    """Loads the YAML configuration file."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def main():
    """Main function to run the chess experiment."""
    parser = argparse.ArgumentParser(description="Run The Deceptive Gambit chess experiment.")
    parser.add_argument('--num-games', type=int, default=None, help='Number of games to play per persona. Overrides config.')
    parser.add_argument('--persona', type=str, help='Run for a single, specified persona.')
    parser.add_argument('--pilot', action='store_true', help='Run a pilot experiment using pilot_num_games from config.')
    args = parser.parse_args()

    print("--- The Deceptive Gambit ---")
    
    # 1. Load configuration
    config = load_config()
    print("Configuration loaded.")

    # 2. Initialize the database session factory
    db_path = Path(config['paths']['database'])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    Session = database.init_db(db_path)
    print(f"Database initialized at: {db_path}")

    # 3. Initialize the LLM Handler
    # This will load the gpt-oss-20b model into the GPU. This may take a few minutes.
    print("Initializing LLM Handler and loading model into GPU memory...")
    llm_handler = LLMHandler(config=config)
    print("Model loaded successfully.")

    # 4. Determine which personas and how many games to run
    if args.persona:
        if args.persona not in config['personas']:
            raise ValueError(f"Persona '{args.persona}' not found in config.yaml")
        personas_to_run = [args.persona]
    else:
        # Default to all personas if none are specified
        personas_to_run = config['personas'].keys()

    if args.num_games:
        num_games_to_run = args.num_games
    elif args.pilot:
        num_games_to_run = config['experiment']['pilot_num_games']
    else:
        num_games_to_run = config['experiment']['full_num_games']

    print(f"\nStarting experiment for personas: {', '.join(personas_to_run)}")
    print(f"Number of games per persona: {num_games_to_run}\n")

    # 5. Core Experiment Loop
    for persona_name in personas_to_run:
        if config['personas'][persona_name]['generation_method'] == 'none':
            print(f"--- Skipping Persona: {persona_name} (Control Group) ---")
            continue

        print(f"--- Running Persona: {persona_name} ---")
        for i in range(num_games_to_run):
            print(f"Starting game {i + 1} of {num_games_to_run} for persona {persona_name}...")
            db_session = Session()
            try:
                game_manager = GameManager(
                    config=config,
                    db_session=db_session,
                    llm_handler=llm_handler,
                    persona_name=persona_name,
                )
                game_manager.play_game()
            except Exception as e:
                print(f"An error occurred during game {i + 1} for {persona_name}: {e}")
            finally:
                db_session.close()
    
    print("\n--- Experiment Finished ---")

if __name__ == "__main__":
    main()