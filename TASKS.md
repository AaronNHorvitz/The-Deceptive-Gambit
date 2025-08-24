# Project Tasks: The Deceptive Gambit

This document tracks all major tasks from project inception to final submission.

---

## Phase 1: Project Setup & Planning 

- [x] **Task 1.1:** Initial Brainstorming & Experimental Design.
- [x] **Task 1.2:** Technology Stack Selection & Pivots:
    - [x] **Task 1.2.1:** Initial decision for `vLLM` backend.
    - [x] **Task 1.2.2:** Pivoted to Hugging Face `Transformers`.
    - [x] **Task 1.2.3:** Final pivot to the robust `Ollama` architecture.
- [x] **Task 1.3:** Project Structuring: Design and finalize the repository file architecture.
- [x] **Task 1.4:** GitHub Repository Setup & Team Collaboration.
- [x] **Task 1.5:** Initial Documentation:
    - [x] **Task 1.5.1:** Create `README.md`.
    - [x] **Task 1.5.2:** Create `docs/EXPERIMENTAL_DESIGN.md`.
    - [x] **Task 1.5.3:** Create `docs/DEVELOPMENT_SETUP.md`.
    - [x] **Task 1.5.4:** Create `docs/FILE_ARCHITECTURE.md`.
    - [x] **Task 1.5.5:** Create and commit the `LICENSE` file.
- [x] **Task 1.6:** Initial Configuration:
    - [x] **Task 1.6.1:** Create `config.yaml`.
    - [x] **Task 1.6.2:** Create `requirements.txt`.
- [x] **Task 1.7:** Environment Setup:
    - [x] **Task 1.7.1:** Install system-level dependencies (`Ollama`, `Stockfish`).
    - [x] **Task 1.7.2:** Create and provision the Python virtual environment.
    - [x] **Task 1.7.3:** Pull required models (`gpt-oss:20b`, `gemma:2b`) via Ollama.

---

## Phase 2: Core Development & Unit Testing 

- [x] **Task 2.1:** Database Module (`src/gambit/database.py`):
    - [x] **Task 2.1.1:** Define SQLAlchemy models (`Game`, `Move`).
    - [x] **Task 2.1.2:** Implement functions to initialize the DB and log game data.
- [x] **Task 2.2:** Database Unit Tests (`src/tests/test_database.py`):
    - [x] **Task 2.2.1:** Write tests for DB creation and table schemas.
    - [x] **Task 2.2.2:** Write tests for game creation and move logging.
- [x] **Task 2.3:** LLM Handler Module (`src/gambit/llm_handler.py`):
    - [x] **Task 2.3.1:** Implement a reusable client for the Ollama server.
    - [x] **Task 2.3.2:** Implement robust regex-based response parsing.
- [x] **Task 2.4:** LLM Handler Unit Tests (`src/tests/test_llm_handler.py`):
    - [x] **Task 2.4.1:** Write tests to mock the `Ollama` client and verify response parsing.
- [x] **Task 2.5:** Game Manager Module (`src/gambit/game_manager.py`):
    - [x] **Task 2.5.1:** Implement the core orchestration logic for a two-player game.
    - [x] **Task 2.5.2:** Integrate `python-chess` for board state and move validation.
    - [x] **Task 2.5.3:** Implement logic to handle illegal moves.
- [x] **Task 2.6:** Game Manager Unit Tests (`src/tests/test_game_manager.py`):
    - [x] **Task 2.6.1:** Write tests to verify game initialization and state transitions.
    - [x] **Task 2.6.2:** Write tests for both legal and illegal move handling.

---

## Phase 3: Integration & Experimentation 

- [x] **Task 3.1:** Main Script Integration (`main.py`): Integrate all modules into a single, executable script.
- [ ] **Task 3.2:** Pilot Experiment Run:
    - [ ] **Task 3.2.1:** Run a successful smoke test (`--num-games 1`) to confirm the end-to-end system is working.
    - [ ] **Task 3.2.2:** Launch the full pilot run (`--pilot`) to gather initial data.
- [ ] **Task 3.3:** (Stretch Goal) LoRA Fine-Tuning:
    - [ ] **Task 3.3.1:** Curate a dataset for the "Arrogant Grandmaster" persona.
    - [ ] **Task 3.3.2:** Fine-tune the `gemma:2b` model with LoRA.
- [ ] **Task 3.4:** Full-Scale Experiment:
    - [ ] **Task 3.4.1:** Launch the final, full run with the best configuration.

---

## Phase 4: Analysis & Submission ▶

- [ ] **Task 4.1:** Data Analysis (`notebooks/002_final_analysis.ipynb`).
- [ ] **Task 4.2:** Kaggle Submission Preparation (Findings files, Writeup).
- [ ] **Task 4.3:** Final Team Review & Submission before the **August 26, 2025 deadline.**