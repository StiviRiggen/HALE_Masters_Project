import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

import utilities as utl
import path_map as p_m
from matplotlib.ticker import FuncFormatter, FixedLocator

# Set global plot parameters for better readability
mpl.rcParams['axes.labelsize'] = 27   # x and y labels          # 27 # 18
mpl.rcParams['axes.titlesize'] = 22   # axes title              # 22 #
mpl.rcParams['xtick.labelsize'] = 25  # x-axis tick labels      # 25 # 16 
mpl.rcParams['ytick.labelsize'] = 25  # y-axis tick labels      # 25 # 16
mpl.rcParams['font.size'] = 22        # default for all text    # 22 #


"""
This files contains functions for plotting multiple simulations trails together. 

1. Save simulation runs as .csv files (Done automatically if save_trails_csv=True in main.py)
2. Open .csv files and extract trails data at the bottom of this file.
3. Plot trails together with the background map as a base layer.
    # Parameter settings:
    - heatmap = True                # If True, a heatmap of the trails is created. Is "show_only_end_points" is also True, then only the endpoints of the trails are plotted in the heatmap.
    - heatmap_multi = True          # If True, trails are plotted as separate heatmaps with different colors
    - show_only_end_points = True   # To show only the end points and not the heatmap, set heatmap=false and show_only_endpoints=True.
"""

# Function to open .csv files containing trails data for multiple simulations
def open_trails_csv(file_path):
    df = pd.read_csv(file_path)
    trails = []
    for sim in df['sim'].unique():
        sim_trail = df[df['sim'] == sim][['x', 'y']].values.tolist()
        trails.append(sim_trail)
    return trails # trails output [sim][step][x/y]

def plot_heatmap_rgb(ax, trail_array, extent, end_point_only=True, bins=200, origin="upper", cmap=None, alpha=1):
    # Assign a fixed color to each trail set (R, G, B)
    colors = [
        [1, 0, 0], # Red
        [0, 1, 0], # Green
        [0, 0, 1], # Blue
    ]
    
    # Create an empty RGB grid (bins x bins x 3)
    rgb_composite = np.zeros((bins, bins, 3))

    for i, trails in enumerate(trail_array):
        if end_point_only:
            pts = np.asarray([np.asarray(t, float)[-1] for t in trails])  # (N_agents,2) - Picks only the last point of each trail
        else:
            pts = np.concatenate([np.asarray(t, float) for t in trails], axis=0)  # (N_total_steps, 2) - stacks all points from all trails together so that the heatmap is based on all points along the trails, not just the endpoints.

        H, xedges, yedges = np.histogram2d(
            pts[:, 0], pts[:, 1],
            bins=bins, 
            range=[[extent[0], extent[1]], [extent[2], extent[3]]]
        )
        
        # Orient and Normalize
        H = H.T
        if origin == "upper": H = np.flipud(H)
        H = np.log1p(H)
        if H.max() > 0: H /= H.max()
            
        # Add this heatmap to its assigned color channel
        color = np.array(colors[i % len(colors)])
        rgb_composite += H[:, :, np.newaxis] * color

    # Ensure values stay between 0 and 1
    rgb_composite = np.clip(rgb_composite, 0, 1)
    
    return ax.imshow(rgb_composite, extent=extent, origin=origin,
                     alpha=alpha, interpolation="bilinear")

def plot_heatmap(ax, trails, extent, end_point_only=True, bins=200, origin="upper", cmap="hot", alpha=0.35):
    """
    Draw a heat map of endpoint density over an existing axes with a base map.
    - trails: list of UTM x and y coordinates of endpoints if end_point_only=True,
              otherwise list of polyline trails (each [(lon,lat),...]).
    """

    # Gather endpoints
    if end_point_only:
        pts = np.asarray([np.asarray(t, float)[-1] for t in trails])  # (N_agents,2) - Picks only the last point of each trail
    else:
        pts = np.concatenate([np.asarray(t, float) for t in trails], axis=0)  # (N_total_steps, 2) - stacks all points from all trails together so that the heatmap is based on all points along the trails, not just the endpoints.

    # 2D histogram in map coords (lon, lat) over the full map extent:
    H, xedges, yedges = np.histogram2d(
        pts[:, 0], pts[:, 1],
        bins=bins, 
        range=[[extent[0], extent[1]], [extent[2], extent[3]]]
    )

    # Orient for imshow: rows = y, cols = x; match base image origin
    H = H.T                                  # (ny, nx)
    if origin == "upper":
        H = np.flipud(H)                     # align with origin='upper'

    # Normalize
    H = np.log1p(H)
    if H.max() > 0:
        H = H / H.max()

    # Plotting histogram as a heatmap
    im = ax.imshow(H, extent=extent, origin=origin, cmap=cmap,
                   alpha=alpha, interpolation="none")
    return im

# Function to plot trails from multiple simulations
def plot_endpoints_heatmap(ax, trails, extent, end_point_only=True,
                           bins=200, origin="upper", cmap="hot", alpha=0.35):
    """
    Draw a heat map of endpoint density over an existing axes with a base map.
    - trails: list of (lon,lat) endpoints if end_point_only=True,
              otherwise list of polyline trails (each [(lon,lat),...]).
    - extent: (minlon, maxlon, minlat, maxlat) used by your base imshow.
    - origin: use the SAME origin as your base raster (likely 'upper').
    """
    # Gather endpoints
    if end_point_only:
        pts = np.asarray(trails, dtype=float)            # (N,2)
    else:
        pts = np.array([np.asarray(t, float)[-1] for t in trails], dtype=float)  # (N,2)

    # Drop any NaNs
    if pts.size == 0:
        return None
    pts = pts[~np.isnan(pts).any(axis=1)]
    if pts.size == 0:
        return None

    # 2D histogram in map coords (lon, lat) over the full map extent
    H, xedges, yedges = np.histogram2d(
        pts[:, 0], pts[:, 1],
        bins=bins,
        range=[[extent[0], extent[1]], [extent[2], extent[3]]]
    )

    # Orient for imshow: rows = y, cols = x; match base image origin
    H = H.T                                  # (ny, nx)
    if origin == "upper":
        H = np.flipud(H)                     # align with origin='upper'

    # Normalize (log helps when counts vary a lot)
    H = np.log1p(H)
    if H.max() > 0:
        H = H / H.max()

    im = ax.imshow(H, extent=extent, origin=origin, cmap=cmap, 
                   alpha=alpha, interpolation="bilinear", rasterized=True) # bilinear
    return im

    
def plotting_UTM(trails, dtm_arr, dtm_extent, start_coord, end_coord, heatmap, plot_save_path, color_bar=False, autosize=False, save_plots=False, normalize_plot=False):
    """
    dtm_arr:        Digital terrain map image as background for plot
    dtm_trf:         Info on map location
    h_start_lat:    Hiker starting location latitude
    h_start_long:   Hiker starting location longditude
    
    heatmap:        Boolean for ploting heatmap or not. (True/False)
    trails:         Input of simulation movement trails.
    """
    print("Starting plot")
    # Plot background map and the starting point location as a green dot.
    fig, ax = plt.subplots(figsize=(13, 13))
    if dtm_arr is not None:
        if dtm_arr.shape[0] == 3 or dtm_arr.shape[0] == 4:        # Handles if input is RGB image (e.g. background map) instead of single band DTM
            dtm_arr = np.moveaxis(dtm_arr, 0, -1)  # (bands, H, W) -> (H, W, bands)
            dtm_arr = dtm_arr.astype(np.uint8)
            im = ax.imshow(dtm_arr, cmap="gray", origin="upper", extent=dtm_extent)
        else:
            im = ax.imshow(dtm_arr, cmap="terrain", origin="upper", extent=dtm_extent, alpha=1)

    ax.scatter(start_coord[0], start_coord[1], s=100, marker="o", edgecolor="black", facecolor="green", zorder=5)

    if color_bar:
        fig.colorbar(im, ax=ax, label="Elevation (m)")

    show_only_end_points = heatmap # To show only the end points and not the heatmap, set heatmap=false and show_only_endpoints=True.

    # If simulation and plot is set to heatmap - plot a heatmap of the endpoints
    if heatmap:
        pts = np.asarray(trails, dtype=float)   # shape (N, 2)
        im = plot_endpoints_heatmap(ax, trails, dtm_extent, end_point_only=show_only_end_points, bins=250, origin="upper", cmap="hot", alpha=1)

        if autosize:
            # Robust zoom around endpoints
            minlon = np.nanmin(pts[:, 0]); maxlon = np.nanmax(pts[:, 0])
            minlat = np.nanmin(pts[:, 1]); maxlat = np.nanmax(pts[:, 1])
            pad_m = 500 # padding from the outermost results (m)
            lat0 = float(np.nanmean(pts[:, 1]))
            cosphi = max(np.cos(np.deg2rad(lat0)), 1e-6)  # guard near poles
            pad_lon = pad_m / (111_320.0 * cosphi)
            pad_lat = pad_m / 111_320.0
            ax.set_xlim(minlon - pad_lon, maxlon + pad_lon)
            ax.set_ylim(minlat - pad_lat, maxlat + pad_lat)
        
        #ax.set_xlim(dtm_extent[0]+3450, dtm_extent[1]-2900)     # Manually set limits to better show heatmap area for 5 min simulations
        #ax.set_ylim(dtm_extent[2]+3150, dtm_extent[3]-3150)

    # Else, plot the trails each simulation took with the end points as red dots.
    else:
        for t in trails:
            t = np.asarray(t, dtype=float)         # shape (T, 2)
            ax.plot(t[:, 0], t[:, 1], linewidth=0.8)
            #ax.scatter(t[:, 0], t[:, 1], s=60, marker="o", edgecolor="black", facecolor="yellow", zorder=5) # Uncomment this line to see each point along the agents path
            ax.scatter(t[-1, 0], t[-1, 1], s=80, marker="o", edgecolor="black", facecolor="red", zorder=5)

        #for i, _ in enumerate(extra_endpoints):
        #    for p in extra_endpoints[i]:
        #        ax.scatter(p[0], p[1], s=60, marker="o", edgecolor="black", facecolor="blue", zorder=4)

        if autosize:
            # Optional: zoom around all trails
            all_lon = np.concatenate([np.asarray(t)[:,0] for t in trails])
            all_lat = np.concatenate([np.asarray(t)[:,1] for t in trails])
            pad = 500 # padding from the outermost results (m)
            ax.set_xlim(all_lon.min() - pad, all_lon.max() + pad)
            ax.set_ylim(all_lat.min() - pad, all_lat.max() + pad)
    
    # Plot the find location as a yellow dot - TODO: Add a variable that turns this on?
    ax.scatter(FindLoc[0], FindLoc[1], s=100, marker="o", edgecolor="black", facecolor="yellow", zorder=6, label="Find location")

    if normalize_plot:
        half_delta_x = int((dtm_extent[1]-dtm_extent[0]) / 2)
        half_delta_y = int((dtm_extent[2]-dtm_extent[3]) / 2)

        center_x = LKP[0] #dtm_extent[1] - half_delta_x # Replace with comment to center around center of the map.
        center_y = LKP[1] #dtm_extent[2] - half_delta_y

        offsets = np.arange(-half_delta_x-5, half_delta_x+5, 4000)

        tick_locations_x = center_x + offsets
        tick_locations_y = center_y + offsets

        ax.xaxis.set_major_locator(FixedLocator(tick_locations_x))
        ax.yaxis.set_major_locator(FixedLocator(tick_locations_y))

        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{int((x - center_x)/1000)} km'))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda y, pos: f'{int((y - center_y)/1000)} km'))

    ax.set_xlabel("Meters x")
    ax.set_ylabel("Meters y")

    #ax.set_xlabel("UTM East")
    #ax.set_ylabel("UTM North")                                
    ax.set_aspect("equal")
    if save_plots:
        plt.tight_layout()
        plt.savefig(f"{plot_save_path}Test.pdf", dpi=300, format="pdf")
        print(f"\nPlot saved as: Test.pdf")
    else:
        plt.tight_layout(); plt.show()


### Main ###

# Open paths and map data
dtm_path, _, _, _, _, _, _, _, _, background_map_path = p_m.open_paths()
_, _, _, dtm_extent, _, _ = utl.open_raster_UTM(dtm_path)
background_map_arr = None #utl.open_raster_image(background_map_path)

trail_array = []

# Collect simulations trails that are to be plotted together and append to trail_array.
trails1 = open_trails_csv("C:\\Users\\Robert\\OneDrive\\Documents\\### UiO\\Masters\\Dokumentation\\#MAIN_RESULTS\\MI_CFG\\Hardangervidda\\Plot_MI_CFG_Hardangervidda_Mental_Illness_2_10000_trails.csv")
trail_array.append(trails1)
#trails2 = open_trails_csv("C:\\MastersProgging\\Master_Project_main\\output\\Plot_02-All_functions_on_trails.csv")
#trail_array.append(trails2)
#trails3 = open_trails_csv("C:\\MastersProgging\\Master_Project_main\\output\\Plot_03-DDA_trails.csv")
#trail_array.append(trails3)

trail_arr = np.asarray(trail_array)
trail_arr = trail_arr.squeeze()


LKP = (83401.39, 6686097.50)
FindLoc = (83377.79, 6686141.87)

# Set plotting parameters
heatmap = True             # If True, only end point is recorded for heatmap
heatmap_multi = False       # If True, trails are plotted as separate heatmaps with different colors, if False, all trails are plotted together in the same heatmap.
show_only_end_points = False # To show only the end points and not the heatmap, set heatmap=false and show_only_endpoints=True.
save_plots = True          # If True, plots are saved as .pdf files NOTE: If True, plots will not be shown.
normalize = True

# Plotting function.
plotting_UTM(trail_arr, background_map_arr, dtm_extent, LKP, FindLoc, heatmap=heatmap, plot_save_path="C:\\MastersProgging\\Master_Project_main\\output\\", color_bar=False, autosize=False, save_plots=save_plots, normalize_plot=normalize)


