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
├── .gitattributes
├── .gitignore
├── LICENSE
├── README.md
├── TASKS.md
├── config.yaml
├── main.py
└── requirements.txt
```

## Directory Breakdown

```
The-Deceptive-Gambit/
|
├── .venv/                     # Python virtual environment (ignored by Git)
|
├── assets/
│   └── results_chart.png      # Image assets for documentation
|
├── data/
│   └── games.db               # SQLite database for storing all game results
|
├── docs/
│   ├── DEVELOPMENT_SETUP.md   # Guide for setting up the development environment
│   ├── EXPERIMENTAL_DESIGN.md # Detailed experimental plan and methodology
│   ├── FILE_ARCHITECTURE.md   # This file
│   └── research_papers/       # Directory for relevant background research
│       └── paper1.pdf
|
├── notebooks/                 # Exploratory and analytical notebooks
│   ├── 001_game_mechanics_test.ipynb
│   ├── 002_full_experiment_run.ipynb
│   └── 003_results_analysis.ipynb
|
├── src/                       # Main source code directory
│   ├── gambit/                # The core Python package for the project
│   │   ├── init.py
│   │   ├── database.py
│   │   ├── game_manager.py
│   │   └── llm_handler.py
│   │

│   └── tests/                 # Unit tests for the gambit package
│       ├── init.py
│       ├── test_database.py
│       ├── test_game_manager.py
│       └── test_llm_handler.py
|
├── .gitattributes             # Defines attributes for Git paths
├── .gitignore                 # Specifies intentionally untracked files
├── LICENSE                    # The CC0 1.0 Universal license file
├── README.md                  # The main project overview
├── TASKS.md                   # The detailed project task list
├── config.yaml                # Central place for all parameters
├── main.py                    # Main executable script to run the experiment
└── requirements.txt           # Python package dependencies
```
