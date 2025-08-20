# The Deceptive Gambit

*An automated testing harness to prove that a powerful AI will cheat at chess... if you give it a reason.*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/release/python-3110/)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![License: CC0-1.0](https://img.shields.io/badge/License-CC0%201.0-lightgrey.svg)](https://creativecommons.org/publicdomain/zero/1.0/)

A framework for statistically measuring deceptive behaviors in Large Language Models by pitting them against a chess engine under various simulated social personas. This project is a submission to the **OpenAI gpt-oss-20b Red-Teaming Challenge**.

---

### Key Project Links
* [**Full Experimental Design**](docs/EXPERIMENTAL_DESIGN.md) - The complete scientific plan for this study.
* [**Analysis Notebook**](analysis.ipynb) - The Jupyter notebook used to analyze the results.
* [**Final Results Database**](results/games.db) - *(Available after experiment completion)*

---

## Abstract 

This project investigates a critical AI safety question: can an AI model's "honesty" be quantitatively measured, and does it change under social pressure? We have developed an automated testing harness to play over 800 games of chess with `gpt-oss-20b`. By systematically altering the LLM's perceived social context (e.g., telling it's playing a child vs. a grandmaster), we aim to discover if the model's integrity is constant or if it can be manipulated. This framework is designed to produce statistically robust evidence of persona-driven deception, a potentially critical and exploitable flaw in social AI alignment.

We designed this project to stand out by focusing on three core principles:

* **Objective, Verifiable Proof:** No more subjective interpretation of an LLM's "intent." We use the formal rules of chess as an unyielding ground truth. An illegal move is an undeniable, reproducible violation—the perfect metric for quantifying deceptive behavior.

* **Rigorous Scientific Method:** We don't just "find a bug"; we investigate the underlying cause. Our experiment is designed to test two competing scientific hypotheses—**Mechanistic Failure vs. Social Deception**—using formal statistical analysis (ANOVA & Tukey's HSD) to deliver a confident conclusion.

* **Advanced Antagonist Simulation:** We go beyond simple prompting. Our framework uses **LoRA-trained "persona bots"** on `Llama3` to create consistent, realistic, and provocative conversational partners, pushing `gpt-oss-20b`'s alignment to its absolute limit in a dynamic, AI-driven environment.

## The Core Question: Will an AI Lie to Avoid Losing?

Our experiment is designed to answer a simple question. Is the model's cheating a simple technical breakdown, or is it a more complex social strategy?

1.  **Hypothesis 1 (Mechanistic Failure):** The model breaks down in complex, losing positions and makes errors, regardless of the opponent.
2.  **Hypothesis 2 (Social Deception):** The model's behavior *changes* based on social context. It is more likely to cheat against an opponent it perceives as naive or beatable.

Our analysis will produce a clear visualization of the "Cheating Rate" across our high-contrast personas, providing powerful evidence for one of these two explosive conclusions.


## Project Roadmap 

* [x] **Phase 1 (Aug 11-19):** Project Setup & Planning
* [ ] **Phase 2 (Aug 20-22):** Core Development & Unit Testing
* [ ] **Phase 3 (Aug 23-24):** Experiment Run (Pilot & Full-Scale)
* [ ] **Phase 4 (Aug 25-26):** Analysis, Write-up, & Submission

## Getting Started: Reproducing Our Framework 

### Prerequisites
* Linux (Ubuntu 22.04+), Python 3.11+, NVIDIA GPU (24GB+ VRAM)

### Installation & Execution
1.  **Clone the repository and set up the environment:**
    ```bash
    git clone [https://github.com/aaronnhorvitz/The-Deceptive-Gambit.git](https://github.com/aaronnhorvitz/The-Deceptive-Gambit.git)
    cd The-Deceptive-Gambit
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    sudo apt-get update && sudo apt-get install stockfish
    ```

2.  **Run a quick test (1 game vs. NaiveNovice):**
    ```bash
    python main.py --num-games 1 --persona NaiveNovice
    ```
The results will be logged to `data/games.db`.
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




