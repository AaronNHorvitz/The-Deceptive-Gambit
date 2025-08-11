# The Deceptive Gambit

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

## The Core Hypothesis: Uncovering Quantifiable Deception

Can we prove that an LLM will cheat? Our experiment is designed to answer this question. We hypothesize that the model's "Cheating Rate"—the frequency of objectively illegal chess moves—is not uniform. We expect to see a statistically significant increase in deceptive moves when the model perceives its opponent as naive, or when it is placed in a position of social rivalry.

Our analysis is designed to produce a clear visualization of this effect, similar to the conceptual chart below, which would provide powerful evidence of a deep, context-aware flaw in the model's behavior.


## Project Roadmap 

* [x] **Aug 11-13:** Initial setup complete. Repo created, environment configured, and `gpt-oss-20b` running locally via `vLLM`.
* [ ] **Aug 14-18:** Develop and debug the core testing harness (game loop, persona injection, data logging).
* [ ] **Aug 19-22:** Run the full experiment (100+ games per persona).
* [ ] **Aug 23-24:** Analyze data, generate visualizations, and identify key findings.
* [ ] **Aug 25:** Draft final Kaggle writeup and prepare submission files.
* [ ] **Aug 26:** Final review and submission.

## Getting Started: Reproducing Our Framework 

### Prerequisites

* Linux (Ubuntu 22.04+ recommended)
* Python 3.11+
* An NVIDIA GPU with 24GB+ VRAM and corresponding drivers installed.
* The `gpt-oss-20b` model weights (downloaded as per competition instructions).

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/aaronnhorvitz/The-Deceptive-Gambit.git](https://github.com/aaronnhorvitz/The-Deceptive-Gambit.git)
    cd The-Deceptive-Gambit
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install the Stockfish chess engine:**
    ```bash
    sudo apt-get update
    sudo apt-get install stockfish
    ```

### Running the Experiment

To run the full experiment for all personas (this may take several hours):
```bash
python main.py --num-games 100 --all-personas
```

### To run a quick test with just one persona:

```bash
python main.py --num-games 5 --persona NaiveNovice
```

The results will be logged to `results/games.db`. To generate the analysis plots and tables from the database, run the analysis notebook:

```bash
jupyter notebook analysis.ipynb
```
---
How about this for the project structure?

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
│   └── gambit/
│       ├── __init__.py
│       ├── database.py
│       ├── game_manager.py
│       └── llm_handler.py
|
├── .gitattributes
├── .gitignore
├── LICENSE                      # The CC0 License file
├── README.md
├── TASKS.md
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




