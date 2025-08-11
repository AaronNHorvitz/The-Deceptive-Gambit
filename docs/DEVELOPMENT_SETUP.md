# Development Environment Setup

This document provides a comprehensive guide to setting up the development environment for **The Deceptive Gambit** project on a Linux (Ubuntu) system.

---

## 1. Prerequisites 

Before you begin, ensure your system meets the following requirements:

* **Operating System:** A modern Linux distribution. Ubuntu 22.04 LTS is recommended and tested.
* **Hardware:** An NVIDIA GPU with at least 24GB of VRAM (e.g., RTX 3090, RTX 4090, A100).
* **Software:** `git` and `python` (version 3.11 or higher) must be installed.

---

## 2. Step-by-Step Installation Guide 

### Step 1: Install System Dependencies

First, update your package list and install the essential system-level software: the Stockfish chess engine and the Python virtual environment package.

```bash
sudo apt-get update
sudo apt-get install stockfish python3.11-venv
```

**NVIDIA Drivers:** Ensure you have the latest stable NVIDIA drivers installed for your GPU. The recommended method is to use Ubuntu's built-in "Software & Updates" utility:

1. Open "Software & Updates."
2. Navigate to the "Additional Drivers" tab.
3. Select the latest tested, proprietary driver (e.g., nvidia-driver-550).
4. Apply changes and reboot your system.

### Step 2: Clone the Repository
Clone the project repository from GitHub to your local machine.

```bash
git clone [https://github.com/aaronnhorvitz/The-Deceptive-Gambit.git](https://github.com/aaronnhorvitz/The-Deceptive-Gambit.git)
cd The-Deceptive-Gambit
```

## Step 3: Set Up the Python Virtual Environment

We use a Python virtual environment (`.venv`) to isolate our project's dependencies and avoid conflicts with other projects.

1. **Create the virtual environmnet:**

```bash
python3 -m venv .venv
```

This command creates a `.venv` directory in the project root. This directory is already included in `.gitignore`.

2. **Activate the virtual environment:**

```bash
source .venv/bin/activate
```

After activation, your terminal prompt will be prefixed with (`.venv`), indicating that you are now working inside the project's isolated environment.

## Step 4: Install Python Dependencies

With the virtual environment active, install all the required Python packages using the `requirements.txt` file. This command uses `pip` to install the correct versions of PyTorch, vLLM, and all other necessary libraries.

```bash
pip install -r requirements.txt
```
## Step 5: Download the LLM Model Weights

This project requires the `gpt-oss-20b` model weights to run locally.

- Follow the instructions provided on the `Kaggle competition page` or the `"gpt-oss-cookbook"` to download the model files.
- Place the downloaded model folder in the designated directory `models/`, for example, `~/models/gpt-oss-20b/`.
- Update the `model.identifier` path in your `config.yaml` file to point to this local directory.

# 3. Verify the Setup

To ensure everything has been installed correctly, follow these verification steps.

## Verify GPU Access in PyTorch

Run the following Python command directly in your activated terminal. It should report success and print your GPU's name.

```bash
python -c "import torch; print(f'PyTorch CUDA available: {torch.cuda.is_available()}'); print(f'Device Name: {torch.cuda.get_device_name(0)}' if torch.cuda.is_available() else '')"
```
## Run a Quick Test of the Experiment

The ultimate test is to run a single game. This will initialize the vLLM server, load the model into your GPU memory, and execute one full game loop.

```bash
python main.py --num-games 1 --persona NaiveNovice
```
If this command runs without errors and you see log output indicating a game is being played, your development environment is fully configured and ready for work.
