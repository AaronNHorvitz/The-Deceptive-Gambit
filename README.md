# The Deceptive Gambit

*An automated testing harness to prove that a powerful AI will cheat at chess... if you give it a reason.*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![License: CC0-1.0](https://img.shields.io/badge/License-CC0%201.0-lightgrey.svg)](https://creativecommons.org/publicdomain/zero/1.0/)

This project is a submission to the **OpenAI gpt-oss-20b Red-Teaming Challenge**.

---

### Key Project Links
* [**Full Experimental Design**](docs/EXPERIMENTAL_DESIGN.md) - The complete scientific plan for this study.
* [**Detailed File Architecture**](docs/FILE_ARCHITECTURE.md) - A breakdown of the repository structure.
* [**Analysis Notebook**](notebooks/003_results_analysis.ipynb) - The Jupyter notebook used to analyze the results.

---

## Overview

This project investigates a critical AI safety question: can an AI model's "honesty" be quantitatively measured, and does it change under social pressure? We have developed an automated testing harness to run **hundreds of games of chess** with `gpt-oss-20b`. By systematically altering the LLM's perceived social context, we aim to produce statistically robust evidence of persona-driven deception.

Our approach is defined by three core principles:

* **Objective, Verifiable Proof:** We use the formal rules of chess as an unyielding ground truth. An illegal move is an undeniable, reproducible violation.

* **Rigorous Scientific Method:** We investigate the underlying cause by testing two competing hypotheses—**Mechanistic Failure vs. Social Deception**—using a data-driven statistical analysis plan to deliver a confident conclusion.

* **Advanced Antagonist Simulation:** Our framework uses the **Ollama** engine to run a `gemma:2b` model as a conversational partner, with plans to fine-tune it with LoRA to create a highly consistent and provocative antagonist.

## The Core Scientific Question

Is the model's cheating a simple technical breakdown, or is it a more complex social strategy? Our experiment is designed to answer this by testing which of two competing hypotheses the data supports:

1.  **Hypothesis 1 (Mechanistic Failure):** The model breaks down and makes errors in complex, losing positions, regardless of the opponent.
2.  **Hypothesis 2 (Social Deception):** The model's behavior *changes* based on social context and is more likely to cheat against an opponent it perceives as naive or beatable.

![Conceptual Results Chart](https://i.imgur.com/uS5wE2H.png)

## Project Roadmap (Deadline: Aug 26)

* [x] **Phase 1 (Aug 20-23):** Project Setup, Refactoring & Planning
* [ ] **Phase 2 (Aug 24):** Core Development & Unit Testing
* [ ] **Phase 3 (Aug 24-25):** Experiment Run (Pilot & Full-Scale)
* [ ] **Phase 4 (Aug 25-26):** Analysis, Write-up, & Submission

## Reproducing Our Framework

### Prerequisites
* Linux (Ubuntu 22.04+), Python 3.11+, NVIDIA GPU (24GB+ VRAM), Git LFS.
* The **Ollama** application must be installed on your system.

### Installation & Setup
1.  **Install System Dependencies:**
    ```bash
    # Install Git LFS for model downloads and Stockfish
    sudo apt-get update && sudo apt-get install git-lfs stockfish
    git lfs install
    ```
2.  **Install Ollama:**
    ```bash
    curl -fsSL [https://ollama.com/install.sh](https://ollama.com/install.sh) | sh
    ```
3.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/aaronnhorvitz/The-Deceptive-Gambit.git](https://github.com/aaronnhorvitz/The-Deceptive-Gambit.git)
    cd The-Deceptive-Gambit
    ```
4.  **Create Python Environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    pip install -e .
    ```
5.  **Pull Models via Ollama:**
    Ensure the Ollama application is running, then pull the required models.
    ```bash
    ollama pull gpt-oss:20b
    ollama pull gemma:2b
    ```

### Running the Experiment
1.  Ensure the Ollama application is running in the background.
2.  Run the smoke test (1 game vs. NaiveNovice):
    ```bash
    python main.py --persona NaiveNovice --num-games 1
    ```
---
## Project Structure
```
The-Deceptive-Gambit/
|
├── .venv/
|
├── assets/
│   └── results_chart.png
|
├── data/
│   └── games.db
|
├── docs/
│   ├── DEVELOPMENT_SETUP.md
│   ├── EXPERIMENTAL_DESIGN.md
│   ├── FILE_ARCHITECTURE.md
│   └── research_papers/
│       └── paper1.pdf
|
├── notebooks/
│   ├── 001_game_mechanics_test.ipynb
│   ├── 002_full_experiment_run.ipynb
│   └── 003_results_analysis.ipynb
|
├── src/
│   ├── gambit/
│   |   ├── __init__.py
│   |   ├── database.py
│   |   ├── game_manager.py
│   |   ├── llm_handler.py
│   |   └── additional files as needed...
│   | 
│   ├── models/
|   |   ├── gemma-2b-it
│   |   └── gpt-oss-20b
│   |  
│   └── tests/
│       ├── __init__.py
│       ├── test_database.py
│       ├── test_game_manager.py
│       ├── test_llm_handler.py
│       └── additional tests as needed...
|
├── .gitattributes
├── .gitignore
├── LICENSE                      # The CC0 License file
├── README.md
├── TASKS.md
├── pyproject.toml
├── config.yaml                  # Central place for all parameters
├── main.py                      # Main executable script
└── requirements.txt             # Python package dependencies
```
---
## Contributors

**Aaron Horvitz, M.S.** 

- Statistician (Data Scientist), RAAS at the Internal Revenue Service
- M.S. Analytics, Texas A&M University
- M.S. Statistical Data Science, Texas A&M University (In Progress)

**Charles Greenwald, PhD, MBA**

- Vice President, Global Biological Platform at NCH Corporation
- PhD in Genetics, Texas A&M University

---
## License
This project is licensed under the CC0 License: [License: CC0-1.0](https://creativecommons.org/publicdomain/zero/1.0/)




