# Development Environment Setup

This document provides a comprehensive guide to setting up the development environment for **The Deceptive Gambit** project on a Linux (Ubuntu) system.

---

## 1. Prerequisites 📋

Before you begin, ensure your system meets the following requirements:

* **Operating System:** A modern Linux distribution. Ubuntu 22.04 LTS is recommended and tested.
* **Hardware:** An NVIDIA GPU is recommended for performance.
* **Software:** `git` and `python` (version 3.11 or higher) must be installed.

---

## 2. Step-by-Step Installation Guide ⚙️

### Step 1: Install System Dependencies & Ollama

This single step installs the `Ollama` application and other necessary tools like the Stockfish chess engine.

```bash
# Install Ollama
curl -fsSL [https://ollama.com/install.sh](https://ollama.com/install.sh) | sh

# Install Stockfish
sudo apt-get update && sudo apt-get install stockfish
```

The Ollama installer will automatically start the server as a background service.

### Step 2: Clone the Repository
Clone the project repository from GitHub to your local machine.

```bash
git clone [https://github.com/aaronnhorvitz/The-Deceptive-Gambit.git](https://github.com/aaronnhorvitz/The-Deceptive-Gambit.git)
cd The-Deceptive-Gambit
```

### Step 3: Set Up the Python Environment

1. **Create and activate the virtual environment:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```


2. **Install all required Python packages:**
```bash
pip install -r requirements.txt
```

3. **Install the project in editable mode:**
```bash
pip install -e .
```

4. **Pull the Required LLM Models:**
```bash
# Pull the target model
ollama pull gpt-oss:20b

# Pull the persona bot model
ollama pull gemma:2b
```

## Final Verification

To confirm your setup is complete, run the project's "smoke test." This will play a single game of chess and verify that all components are working together.

```bash
python main.py --persona NaiveNovice --num-games 1
```

If the script runs and a game plays out in your terminal, your development environment is fully configured and ready for the experiment.