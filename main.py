# Imports from project files
import utilities as utl              
import path_map as p_m
import config as cfg
import update_func
import movement_models as mm
import direction_modifiers as dm
import speed_modifiers as sm
import blockers_and_policies as bp
import plotting as plt

import multiprocessing as mp        # For parallel processing of multiple simulations
from functools import partial       # For passing multiple arguments to the multiprocessing function



##### Open Rasters #####
# Collecting files paths for opening. Handled in path_map.py
dtm_path, wm_path, roads_path, buff_roads_path, forest_path, marsh_path, developed_path, open_area_path, plot_save_path, background_map_path = p_m.open_paths()

# Opening rasters and saving data.
dtm_arr, dtm_tfm, dtm_crs, dtm_extent, dtm_height, dtm_width = utl.open_raster_UTM(dtm_path)
wm_arr, wm_tfm, wm_crs, wm_extent, wm_height, wm_width = utl.open_raster_UTM(wm_path)
roads_arr, roads_tfm, roads_crs, roads_extent, roads_height, roads_width = utl.open_raster_UTM(roads_path)
buff_roads_arr, buff_roads_tfm, buff_roads_crs, buff_roads_extent, buff_roads_height, buff_roads_width = utl.open_raster_UTM(buff_roads_path)
forest_arr, forest_tfm, forest_crs, forest_extent, forest_height, forest_width = utl.open_raster_UTM(forest_path)
marsh_arr, marsh_tfm, marsh_crs, marsh_extent, marsh_height, marsh_width = utl.open_raster_UTM(marsh_path)
developed_arr, developed_tfm, developed_crs, developed_extent, developed_height, developed_width = utl.open_raster_UTM(developed_path)
open_area_arr, open_area_tfm, open_area_crs, open_area_extent, open_area_height, open_area_width = utl.open_raster_UTM(open_area_path)
background_map_arr = utl.open_raster_image(background_map_path)

# Initiating Mapping and Mask information stored in an instance of the MapData dataclass.
MapData = cfg.MapData(

    # DTM data
    dtm_arr=dtm_arr,
    dtm_tfm=dtm_tfm,
    dtm_extent=dtm_extent,

    # Mask data
    wm_arr=wm_arr,
    wm_tfm=wm_tfm,
    buff_roads_arr=buff_roads_arr,
    buff_roads_tfm=buff_roads_tfm,
    roads_arr=roads_arr,
    roads_tfm=roads_tfm,
    forest_arr=forest_arr,
    forest_tfm=forest_tfm,
    marsh_arr=marsh_arr,
    marsh_tfm=marsh_tfm,
    developed_arr=developed_arr,
    developed_tfm=developed_tfm,
    open_area_arr=open_area_arr,
    open_area_tfm=open_area_tfm,
    
    # Plotting and background map data
    plot_save_path=plot_save_path,
    background_map_arr=background_map_arr
)



##### Config instances #####
"""
Initializing parameter configurations. Multiple can be created for multiple simulation runs to be run sequetially.
"""

CFG1 = cfg.CFG(
    config_name = "Test",
    sim_num = 10,
    hours_missing = 3,

    LKP = (146911.53,6843034.76),
    FindLoc = (149696.60,6841378.45),
    )

        

#===================================================================================================
#      Main Code #1
#===================================================================================================
"""
Using the basic outline of the following code, edit from this point to run the simulation required in e.g. a for loop.

Steps:
==============================
1. Initialize plotting parameters
2. Activate simulation model parameters by adding or removing functions from the lists.
3. Run the main function with the desired configuration instance(s).

"""

# Plotting parameters
do_plots = True             # If True, plots are generated
heatmap = True              # If True, only end point is recorded for heatmap
save_plots = True           # If True, plots are saved as .png files NOTE: If True, plots will not be shown.
save_csv = True             # If True, trails data is saved as .csv file for later plotting.
color_bar = False           # If True, color bar is shown on plot
autosize = False            # Determines whether the map will autozoom to the location of the points, if not it will show the entire map area.
normalize_plot = False        # If True, trails will be normalized around the LKP (i.e. LKP will be at (0,0) and all points will be relative to this location). If False, trails will be plotted in their original UTM coordinates.
plot_background = background_map_arr # Choose which map array will be the background for the plots

"""
Activate simulation model parameters:
Add or remove functions from the lists below to activate or deactivate them in the simulation. 
NOTE: The order of the functions gives the simulatin order of prioritation. This is especially important for blockers and block policies, as the first blocker that is triggered will determine the block policy that is applied.
"""

# Main function
# This is the mulitprocesser function. It allows simulations for different CFG instances to be run in parallel across multiple cores.

configs = [CFG1]#, CFG2, CFG3, CFG4]#, CFG5, CFG6, CFG7, CFG8]#, CFG9]#, CFG10, CFG11, CFG12]#, CFG13, CFG14, CFG15]#, CFG16, CFG17, CFG18, CFG19, CFG20, CFG21, CFG22]

# update_func.sim_runner(CFG1, MapData, do_plots, save_csv, heatmap, save_plots, color_bar, autosize, plot_background)

if __name__ == "__main__":

    print(f"Starting {len(configs)} configurations across {mp.cpu_count()} cores...")

    worker_task = partial(
        update_func.sim_runner,
        MapData=MapData,
        do_plots=do_plots,
        save_csv=save_csv,
        heatmap=heatmap,
        save_plots=save_plots,
        color_bar=color_bar,
        autosize=autosize,
        plot_background=plot_background,
        normalize_plot=normalize_plot
    )

    # Run simulations in parallel across configurations
    with mp.Pool() as pool:
        pool.map(worker_task, configs)



#==========================================
# Main code #2
#==========================================
