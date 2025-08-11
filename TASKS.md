
# Project Tasks: The Deceptive Gambit

This document tracks all major tasks from project inception to final submission.

---

## Phase 1: Project Setup & Planning (Completed)

- [x] **Initial Brainstorming:** Define the core concept of testing LLM deception via chess.
- [x] **Experimental Design:** Develop the multi-persona experimental methodology.
- [x] **Technology Stack Selection:** Decide on local GPU inference with `vLLM` and a Python/SQLite backend.
- [x] **Project Structuring:** Design and finalize the repository file architecture.
- [x] **GitHub Repository Setup:** Create the public `The-Deceptive-Gambit` repository.
- [x] **Initial Documentation:**
    - [x] Create `README.md` with project overview and goals.
    - [x] Create `docs/EXPERIMENTAL_DESIGN.md` with the formal scientific plan.
    - [x] Create `docs/FILE_ARCHITECTURE.md`.
    - [x] Create and commit the `LICENSE` file (CC0 1.0 Universal).
- [x] **Initial Configuration:**
    - [x] Create `config.yaml` with all personas and experiment parameters.
    - [x] Create `requirements.txt` with all necessary Python dependencies.
- [x] **Team Collaboration:** Invite Charles Greenwald to the repository.

---

## Phase 2: Core Development & Unit Testing

- [ ] **Database Module (`src/gambit/database.py`):**
    - [ ] Define the SQLAlchemy models for the `games` and `moves` tables.
    - [ ] Implement a function to initialize the database and create tables.
    - [ ] Implement functions to log a new game, a new move, and update game status.
- [ ] **Database Unit Tests (`src/tests/test_database.py`):**
    - [ ] Write tests to verify database creation.
    - [ ] Write tests to verify that logging a move works as expected.
    - [ ] Use an in-memory SQLite database for testing to keep tests fast and isolated.
- [ ] **LLM Handler Module (`src/gambit/llm_handler.py`):**
    - [ ] Create a class to initialize the `vLLM` client.
    - [ ] Implement a method to get a move from the LLM based on a board state and system prompt.
    * [ ] Implement logic to parse the model's output, separating the chess move from the commentary.
- [ ] **LLM Handler Unit Tests (`src/tests/test_llm_handler.py`):**
    - [ ] Write tests to verify that the model's output string is parsed correctly.
    - [ ] "Mock" the `vLLM` call to test the handler's logic without actually needing a GPU.
- [ ] **Game Manager Module (`src/gambit/game_manager.py`):**
    - [ ] Create a class that orchestrates a single game of chess.
    - [ ] Initialize with a specific persona and connection to the database and LLM handler.
    * [ ] Integrate the `python-chess` library to manage board state and validate moves.
    * [ ] Implement the main game loop logic: get engine move, get LLM move, validate, log, repeat.
    - [ ] Implement the "confrontation" logic for when an illegal move is detected.
- [ ] **Game Manager Unit Tests (`src/tests/test_game_manager.py`):**
    - [ ] Write tests to verify game initialization.
    - [ ] Write tests to verify move validation logic (test both legal and illegal moves).
    - [ ] Write tests to ensure the game correctly identifies checkmate and stalemate conditions.

---

## Phase 3: Integration & Experimentation

- [ ] **Main Script Integration (`main.py`):**
    - [ ] Implement the main loops to iterate through personas and game numbers.
    - [ ] Integrate the `GameManager` class.
    - [ ] Add robust error handling and logging.
- [ ] **Pilot Experiment Run:**
    - [ ] Run the experiment with `num-games = 5` for all personas.
    - [ ] Analyze the initial `games.db` file in `notebooks/001_game_mechanics_test.ipynb`.
    - [ ] Debug any issues with the game loop, data logging, or model interaction.
- [ ] **Full-Scale Experiment:**
    - [ ] Launch the full run with `num-games = 100` for all personas.
    - [ ] Monitor the process for any errors. This will take several hours.

---

## Phase 4: Analysis & Submission

- [ ] **Data Analysis (`notebooks/003_results_analysis.ipynb`):**
    - [ ] Load the final `games.db` into a pandas DataFrame.
    - [ ] Clean and process the data.
    - [ ] Calculate the primary and secondary metrics (Cheating Rate, Deception Rate) for each persona group.
    - [ ] Perform the ANOVA and Tukey's HSD statistical tests.
    - [ ] Generate final plots and tables (especially the main results bar chart).
- [ ] **Kaggle Submission Preparation:**
    - [ ] Synthesize key findings from the analysis.
    - [ ] Write the content for up to five `findings.json` files.
    - [ ] Draft the final Kaggle Writeup (max 3,000 words), using the `README.md` and `EXPERIMENTAL_DESIGN.md` as a base.
- [ ] **Final Review:**
    - [ ] Team review of all submission materials (code, writeup, findings).
    - [ ] Final check against all competition rules.
    - [ ] **Submit to Kaggle before the August 26, 2025 deadline.**
