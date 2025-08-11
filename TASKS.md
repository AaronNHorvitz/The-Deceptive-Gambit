# Project Tasks: The Deceptive Gambit

This document tracks all major tasks from project inception to final submission.

---

## Phase 1: Project Setup & Planning ✅

- [x] **Task 1.1:** Initial Brainstorming: Define the core concept of testing LLM deception via chess.
- [x] **Task 1.2:** Experimental Design: Develop the multi-persona experimental methodology.
- [x] **Task 1.3:** Technology Stack Selection: Decide on local GPU inference with `vLLM` and a Python/SQLite backend.
- [x] **Task 1.4:** Project Structuring: Design and finalize the repository file architecture.
- [x] **Task 1.5:** GitHub Repository Setup: Create the public `The-Deceptive-Gambit` repository and invite collaborators.
- [x] **Task 1.6:** Initial Documentation:
    - [x] **Task 1.6.1:** Create `README.md` with project overview and goals.
    - [x] **Task 1.6.2:** Create `docs/EXPERIMENTAL_DESIGN.md` with the formal scientific plan.
    - [x] **Task 1.6.3:** Create `docs/DEVELOPMENT_SETUP.md`.
    - [x] **Task 1.6.4:** Update `docs/FILE_ARCHITECTURE.md` with the final, agreed-upon project structure.
    - [x] **Task 1.6.5:** Create and commit the `LICENSE` file (CC0 1.0 Universal).
- [x] **Task 1.7:** Initial Configuration:
    - [x] **Task 1.7.1:** Create `config.yaml` with all personas and experiment parameters.
    - [x] **Task 1.7.2:** Create `requirements.txt` with all necessary Python dependencies.
    - [x] **Task 1.7.3:** Update the `.gitignore` file to explicitly ignore `src/models/*`, `.ipynb_checkpoints/`, and `__pycache__/`.
    - [x] **Task 1.7.7:** Setup and test the initial development environment per `DEVELOPMENT_SETUP.md`.
---

## Phase 2: Core Development & Unit Testing ⚙️

- [ ] **Task 2.1:** Database Module (`src/gambit/database.py`):
    - [ ] **Task 2.1.1:** Define the SQLAlchemy models (`Game`, `Move`).
    - [ ] **Task 2.1.2:** Implement functions to initialize the database connection and log game data.
- [ ] **Task 2.2:** Database Unit Tests (`src/tests/test_database.py`):
    - [ ] **Task 2.2.1:** Write tests to verify database creation and table schemas.
    - [ ] **Task 2.2.2:** Write tests to verify that creating games and logging moves works as expected, using an in-memory test database.
- [ ] **Task 2.3:** LLM Handler Module (`src/gambit/llm_handler.py`):
    - [ ] **Task 2.3.1:** Create a class to initialize the `vLLM` client and load the model.
    - [ ] **Task 2.3.2:** Implement a method to get a move from the LLM, parsing the output to separate the move notation from the commentary.
- [ ] **Task 2.4:** LLM Handler Unit Tests (`src/tests/test_llm_handler.py`):
    - [ ] **Task 2.4.1:** Write tests to verify the output parsing logic.
    - [ ] **Task 2.4.2:** Mock the `vLLM` call to test the handler's logic without requiring a GPU.
- [ ] **Task 2.5:** Game Manager Module (`src/gambit/game_manager.py`):
    - [ ] **Task 2.5.1:** Create a class to orchestrate a single game of chess.
    - [ ] **Task 2.5.2:** Integrate the `python-chess` library for board state management and move validation.
    - [ ] **Task 2.5.3:** Implement the main game loop logic (engine move -> LLM move -> validation).
    - [ ] **Task 2.5.4:** Implement the "confrontation" logic for handling illegal moves.
- [ ] **Task 2.6:** Game Manager Unit Tests (`src/tests/test_game_manager.py`):
    - [ ] **Task 2.6.1:** Write tests to verify game initialization and state transitions.
    - [ ] **Task 2.6.2:** Write tests to verify the move validation logic for both legal and illegal moves.
    - [ ] **Task 2.6.3:** Write tests to ensure the game correctly identifies end conditions (checkmate, stalemate).

---

## Phase 3: Integration & Experimentation 🔬

- [ ] **Task 3.1:** Main Script Integration (`main.py`):
    - [ ] **Task 3.1.1:** Implement the main loops to iterate through personas and game counts from `config.yaml`.
    - [ ] **Task 3.1.2:** Integrate the `GameManager` class and add robust error handling.
- [ ] **Task 3.2:** Pilot Experiment Run:
    - [ ] **Task 3.2.1:** Run the experiment with `num-games = 5` for all personas.
    - [ ] **Task 3.2.2:** Use `notebooks/002_full_experiment_run.ipynb` to trigger and monitor the pilot.
    - [ ] **Task 3.2.3:** Debug any issues found in the game loop, data logging, or model interaction.
- [ ] **Task 3.3:** Full-Scale Experiment:
    - [ ] **Task 3.3.1:** Launch the full run with `num-games = 100` for all personas.
    - [ ] **Task 3.3.2:** Monitor the process for any errors or performance bottlenecks.

---

## Phase 4: Analysis & Submission 🏁

- [ ] **Task 4.1:** Data Analysis (`notebooks/003_results_analysis.ipynb`):
    - [ ] **Task 4.1.1:** Load the final `games.db` into a pandas DataFrame.
    - [ ] **Task 4.1.2:** Clean, process, and calculate the primary and secondary metrics for each persona group.
    - [ ] **Task 4.1.3:** Perform the ANOVA and Tukey's HSD statistical tests.
    - [ ] **Task 4.1.4:** Generate final plots and tables for the writeup.
- [ ] **Task 4.2:** Kaggle Submission Preparation:
    - [ ] **Task 4.2.1:** Synthesize key findings from the analysis into a compelling narrative.
    - [ ] **Task 4.2.2:** Create up to five `findings.json` files for the most significant exploits.
    - [ ] **Task 4.2.3:** Draft the final Kaggle Writeup (max 3,000 words).
- [ ] **Task 4.3:** Final Documentation Update:
    - [ ] **Task 4.3.1:** Ensure all documentation (`README.md`, `DEVELOPMENT_SETUP.md`, etc.) is finalized and reflects the completed project.
- [ ] **Task 4.4:** Final Review & Submission:
    - [ ] **Task 4.4.1:** Conduct a final team review of all code and submission materials.
    - [ ] **Task 4.4.2:** Complete a final check against all competition rules.
    - [ ] **Task 4.4.3:** **Submit to Kaggle before the August 26, 2025 deadline.**
