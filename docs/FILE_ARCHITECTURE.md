# File Architecture for The Deceptive Gambit

This document outlines the complete file and directory structure for the project.

## Root Directory

The root contains top-level configuration, documentation, and the main entry point for the application.

```
The-Deceptive-Gambit/
├── .venv/
├── assets/
├── data/
├── docs/
├── notebooks/
├── src/
├── .gitignore
├── LICENSE
├── README.md
├── TASKS.md
├── pyproject.toml
├── config.yaml
├── main.py
└── requirements.txt
```

## Directory Breakdown

```
The-Deceptive-Gambit/
├── .venv/                     # Python virtual environment (ignored by Git)
├── assets/
│   └── results_chart.png      # Image assets for documentation
├── data/
│   └── games.db               # SQLite database for storing all game results
├── docs/
│   ├── DEVELOPMENT_SETUP.md   # Guide for setting up the development environment
│   ├── EXPERIMENTAL_DESIGN.md # The formal scientific plan
│   └── FILE_ARCHITECTURE.md   # This file
├── notebooks/                 # Exploratory and analytical notebooks
│   ├── 001_smoke_test.ipynb
│   └── 002_final_analysis.ipynb
├── src/                       # Main source code directory
│   ├── gambit/                # The core Python package for the project
│   │   ├── init.py
│   │   ├── database.py        # Handles all database schema and interactions
│   │   ├── game_manager.py    # Orchestrates the game logic and flow
│   │   └── llm_handler.py     # Handles communication with the Ollama server
│   └── tests/                 # Unit tests for the gambit package
│       ├── init.py
│       ├── test_database.py
│       ├── test_game_manager.py
│       └── test_llm_handler.py
├── .gitattributes             # Defines attributes for Git paths
├── .gitignore                 # Specifies intentionally untracked files
├── LICENSE                    # The CC0 1.0 Universal license file
├── README.md                  # The main project overview
├── TASKS.md                   # The detailed project task list
├── pyproject.toml             # Python project metadata for packaging and tools
├── config.yaml                # Central configuration for all parameters
├── main.py                    # Main executable script to run the experiment
└── requirements.txt           # Python package dependencies
```

---
### Summary of Key Updates
* **Removed `src/models/` Directory:** Since we've pivoted to `Ollama`, the model weights are now managed by the Ollama application in a central system location, not within our project directory. This keeps our repository clean.
* **Cleaned up Formatting:** Tidied up the tree diagram for better readability.
* **Refined Descriptions:** Made the comments for each file more concise and consistent.

With this, all of your core documentation is finalized and aligned.
