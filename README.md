# HALE - Heuristic Agent-based Lost-person Estimator
### Part of my Masters project in Cybernetics and Autonimous Systems

HALE is a python code that uses thousands of simulated agents to generate a heatmap of estimated locations of the lost person.

Running the Demo will result in this output:

![Demo of HALE output heatmap](/output/Plot_2026-05-14_1702_Test_sims=10000_res=60_hours=3.pdf)


## Project Structure
- main.py # Initiate CFG instance(s), set plotting settings by selecting True/False on the variables.

- update_func.py # Handles the simulation runs.

- config.py # Holds the initial CFG class definition with standard values.

- sim_evaluation.py # Handles the evaluation of the simulation results from stored .CSV files.

- movement_models.py # Holds functions to handle the different movement models for the agents

- direction_modifiers.py, speed_modifiers.py # Hold individual functions to apply modifiers

- blockers_and_policies.py # Holds individual functions that handle blockers and their corosponding policies

- utilities.py # Holds different functions that are needed to function globaly

- plotting.py # Handles the plotting of the simulation output

- multi_plotting.py # Handles ploting of simulation runs from .CSV files.

- requirements.txt # Dependencies

- README.md # Project documentation

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/StiviRiggen/HALE_Masters_Project.git

2. (optional) Create virtuel environment

3. Install dependancies
   ```bash
   pip install -r requirements.txt

## Usage

- Run the main script
   ```bash
   python main.py

## Configuration

- Change parameters in the CFG instances, or in the main class in config.py

