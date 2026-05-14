import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from rasterio.transform import array_bounds
from datetime import datetime
from matplotlib.colors import ListedColormap
from matplotlib.ticker import FuncFormatter, FixedLocator

"""#(Small plots)
mpl.rcParams['axes.labelsize'] = 25   # x and y labels
mpl.rcParams['axes.titlesize'] = 22   # axes title
mpl.rcParams['xtick.labelsize'] = 22  # x-axis tick labels
mpl.rcParams['ytick.labelsize'] = 22  # y-axis tick labels
mpl.rcParams['font.size'] = 22        # default for all text"""

# Set global plot parameters for better readability (Full sized plot)
mpl.rcParams['axes.labelsize'] = 20   # x and y labels
mpl.rcParams['axes.titlesize'] = 18   # axes title
mpl.rcParams['xtick.labelsize'] = 18  # x-axis tick labels
mpl.rcParams['ytick.labelsize'] = 18  # y-axis tick labels
mpl.rcParams['font.size'] = 16        # default for all text

# Define a map where 0 = Green and 1 = Blue
# custom_cmap = ListedColormap(['green', 'blue'])

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
                   alpha=alpha, interpolation="bilinear", rasterized=True) #"bilinear"
    return im

    
def plotting_UTM(CFG, dtm_arr, dtm_extent, h_start_long, h_start_lat, heatmap, trails, extra_endpoints, plot_save_path, color_bar=True, autosize=True, save_plots=False, normalize_plot=False):
    """
    dtm_arr:        Digital terrain map image as background for plot
    dtm_trf:         Info on map location
    h_start_lat:    Hiker starting location latitude
    h_start_long:   Hiker starting location longditude
    
    heatmap:        Boolean for ploting heatmap or not. (True/False)
    trails:         Input of simulation movement trails.
    """

    # Plot background map and the starting point location as a green dot.
    fig, ax = plt.subplots(figsize=(12, 12))
    if dtm_arr is not None:
        if dtm_arr.shape[0] == 3 or dtm_arr.shape[0] == 4:        # Handles if input is RGB image (e.g. background map) instead of single band DTM
            dtm_arr = np.moveaxis(dtm_arr, 0, -1)  # (bands, H, W) -> (H, W, bands)
            dtm_arr = dtm_arr.astype(np.uint8)
            im = ax.imshow(dtm_arr, cmap="gray", origin="upper", extent=dtm_extent)
        else:
            im = ax.imshow(dtm_arr, cmap="terrain", origin="upper", extent=dtm_extent, alpha=1)

    ax.scatter(h_start_long, h_start_lat, s=80, marker="o", edgecolor="black", facecolor="green", zorder=5)

    if color_bar:
        fig.colorbar(im, ax=ax, label="Elevation (m)")

    show_only_end_points = heatmap # To show only the end points and not the heatmap, set heatmap=false and show_only_endpoints=True.

    # If simulation and plot is set to heatmap - plot a heatmap of the endpoints
    if heatmap:
        pts = np.asarray(trails, dtype=float)   # shape (N, 2)
        im = plot_endpoints_heatmap(ax, trails, dtm_extent, end_point_only=show_only_end_points, bins=100, origin="upper", cmap="hot", alpha=0.8)

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
            ax.plot(t[:, 0], t[:, 1], linewidth=1.2)    #linewidth=0.8
            #ax.scatter(t[:, 0], t[:, 1], s=60, marker="o", edgecolor="black", facecolor="yellow", zorder=5) # Uncomment this line to see each point along the agents path
            ax.scatter(t[-1, 0], t[-1, 1], s=80, marker="o", edgecolor="black", facecolor="red", zorder=5)

        for i, _ in enumerate(extra_endpoints):
            for p in extra_endpoints[i]:
                ax.scatter(p[0], p[1], s=60, marker="o", edgecolor="black", facecolor="blue", zorder=4)

        if autosize:
            # Optional: zoom around all trails
            all_lon = np.concatenate([np.asarray(t)[:,0] for t in trails])
            all_lat = np.concatenate([np.asarray(t)[:,1] for t in trails])
            pad = 500 # padding from the outermost results (m)
            ax.set_xlim(all_lon.min() - pad, all_lon.max() + pad)
            ax.set_ylim(all_lat.min() - pad, all_lat.max() + pad)
    
    # Plot the find location as a yellow dot - TODO: Add a variable that turns this on?
    ax.scatter(CFG.FindLoc[0], CFG.FindLoc[1], s=60, marker="o", edgecolor="black", facecolor="yellow", zorder=6, label="Find location")

    if normalize_plot:
        """
        If normalize plots is activated, This will remove the UTM coordinates from the output plot and replace them with normalized coords in km with the LKP as 0, 0.
        The center of the map can be used as 0, 0 by swaping start_lat and start_long with the commented coded.
        """
        half_delta_x = int((dtm_extent[1]-dtm_extent[0]) / 2)
        half_delta_y = int((dtm_extent[2]-dtm_extent[3]) / 2)

        center_x = h_start_long #dtm_extent[1] - half_delta_x
        center_y = h_start_lat  #dtm_extent[2] - half_delta_y

        offsets = np.arange(-half_delta_x, half_delta_x, 2000)

        tick_locations_x = center_x + offsets +495
        tick_locations_y = center_y + offsets +495

        ax.xaxis.set_major_locator(FixedLocator(tick_locations_x))
        ax.yaxis.set_major_locator(FixedLocator(tick_locations_y))

        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{int((x - center_x)/1000)} km')) #/1000)} km'))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda y, pos: f'{int((y - center_y)/1000)} km')) #/1000)} km'))

    ax.set_xlabel("km x") #"UTM 33N coordinates x"
    ax.set_ylabel("km y")

    #ax.set_xlabel("UTM East")
    #ax.set_ylabel("UTM North")                                
    ax.set_aspect("equal")
    if save_plots:
        plt.tight_layout()
        now = datetime.now().strftime("%Y-%m-%d_%H%M")
        plt.savefig(f"{plot_save_path}{now}_{CFG.config_name}_sims={CFG.sim_num}_res={CFG.sim_res_sec}_hours={CFG.hours_missing}.pdf", dpi=300, format="pdf")
        print(f"\nPlot saved as: {now}_{CFG.config_name}_sims={CFG.sim_num}_res={CFG.sim_res_sec}_hours={CFG.hours_missing}.pdf")
    else:
        plt.tight_layout(); plt.show()



