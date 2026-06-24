## HALLE – Heuristic Agent-based Lost-person Location Estimator

Part of my Master's project in Cybernetics and Autonomous Systems at the University of Oslo (UiO).

HALLE is a Python-based simulation framework that uses thousands of simulated agents to generate a heatmap of the estimated locations of a lost person.

Running the demo produces an output heatmap similar to:

![Demo of HALLE output heatmap](/output/Plot_2026-05-14_1702_Test_sims=10000_res=60_hours=3.pdf)

---

## Project Structure

- `main.py`  
  Entry point. Initializes `CFG` instance(s) and sets plotting options via boolean variables.

- `update_func.py`  
  Core simulation loop and update functions.

- `config.py`  
  Contains the `CFG` class definition with default configuration values.

- `sim_evaluation.py`  
  Tools for evaluating simulation results stored in `.csv` files.

- `movement_models.py`  
  Functions implementing different agent movement models.

- `direction_modifiers.py`, `speed_modifiers.py`  
  Functions that apply direction and speed modifiers to agents.

- `blockers_and_policies.py`  
  Functions that model blockers (e.g., obstacles, constraints) and their corresponding policies.

- `utilities.py`  
  General utility functions used throughout the project.

- `plotting.py`  
  Functions for plotting simulation outputs.

- `multi_plotting.py`  
  Functions for plotting and comparing multiple simulation runs from `.csv` files.

- `requirements.txt`  
  Python dependencies.

- `README.md`  
  Project documentation (this file).

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/StiviRiggen/HALE_Masters_Project.git
   cd HALE_Masters_Project

2. (optional) Create virtuel environment

4. Install dependancies
   ```bash
   pip install -r requirements.txt

## Usage

- Run the main script
   ```bash
   python main.py

## Configuration

- Change parameters in the CFG instances in the main.py file, or in the configuration class in the config.py file

