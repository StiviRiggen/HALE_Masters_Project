# Lost Hiker Simulation
### Part of masters project

A Python project for simulating random walks, elevation-based movement, and visualizing results (e.g., heatmaps of endpoints).  
Built with `numpy`, `matplotlib`, `rasterio`, `haversine`, and `pyproj`.

---

## Features
- Random walk simulations
- Elevation-aware movement (climbers/declimbers)
- Coordinate transformations with `pyproj`
- Raster data handling with `rasterio`
- Heatmap plotting of hiker endpoints

---

## Project Structure
- main.py # Entry point for running simulations and visualizations

- utilities.py # Helper functions and classes (walkers, raster tools, etc.)

- requirements.txt # Dependencies

- README.md # Project documentation

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/StiviRiggen/Master_Project_main.git

2. (optional) Create virtuel environment

3. Install dependancies
   ```bash
   pip install -r requirements.txt

## Usage

- Run the main script
   ```bash
   python main.py

- Run differrent simulations by calling on the different functions found in `utilities.py` and change parameters by changing the input values for the function.

