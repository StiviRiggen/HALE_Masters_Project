import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from config import CFG
from pathlib import Path
import matplotlib as mpl

# Set global plot parameters for better readability
mpl.rcParams['axes.labelsize'] = 16   # x and y labels
mpl.rcParams['axes.titlesize'] = 18   # axes title
mpl.rcParams['xtick.labelsize'] = 16  # x-axis tick labels
mpl.rcParams['ytick.labelsize'] = 16  # y-axis tick labels
mpl.rcParams['font.size'] = 16        # default for all text

def open_trails_csv(file_path):
    """
    This function opens the .csv files produced by the main simulation function and outputs them as a trails array.
    """
    df = pd.read_csv(file_path)

    trails_arr = np.stack([group[['x', 'y']].to_numpy() for _, group in df.groupby('sim')]).squeeze(1)  # extracts the data in the .csv (Sim, Step, x, y) and outputs an arry [N_sims, [x,y]] shaped (N, 2).

    return trails_arr

def xy_to_rowcol(x, y, extent, shape):
    """
    This function converts normalized x,y coordinates to row and column indexes in the probability map histogram
    """

    xmin, xmax, ymin, ymax = extent
    rows, cols = shape

    # Normalize coordinates to a vlaue between 0 and 1 and multiply by total to find the corosponding row.
    col = int((x - xmin) / (xmax - xmin) * cols)
    row = int((y - ymin) / (ymax - ymin) * rows)

    col = int(np.clip(col, 0, cols - 1))
    row = int(np.clip(row, 0, rows - 1))

    return row, col

def mapscore(prob_map, find_rowcol, pix_factor):

    find_row, find_col = find_rowcol

    p = prob_map[find_row, find_col]    # produces the probability density of the cell that contains the true find location.

    print("Probability density for FindLoc pixel: ", p)

    flat = prob_map.ravel()
    N = flat.size * pix_factor                      # Total number of pixels in the probability map, multiplied by the pix_factor to account for the fact that each pixel represents a larger area than 5x5m. This is used to calculate the rank of the find location pixel in the probability distribution.
    n = np.count_nonzero(flat > p) * pix_factor     # Number of pixels with a higher probability density than the find location pixel, multiplied by the pix_factor for the same reason as above.
    m = np.count_nonzero(flat == p) * pix_factor    # Note: Should multiply with pix_factor for N, n, and m but this cancels itsself out when calculating r.

    r = (n + m / 2) / N
    R = (0.5 - r) / 0.5
    return float(R)

def InlierArea(prob_map, res, pix_factor):

    flat = prob_map.ravel()
    N = flat.size * pix_factor

    R_in = []

    for p in flat:
        n = np.count_nonzero(flat > p) * pix_factor      # Number of pixels with a higher probability density than the find location pixel, multiplied by the pix_factor for the same reason as above.
        m = np.count_nonzero(flat == p) * pix_factor     # Note: Should multiply with pix_factor for N, n, and m but this cancels itsself out when calculating r.

        r = (n + m / 2) / N
        R = (0.5 - r) / 0.5

        if R > 0.1:
            R_in.append(R)
    
    R_num = len(R_in)
    area = R_num * res * res
    area_km = area/1000000

    return print("The area with a score higher than R = 0.1 is ", area_km, " km^2")


def Normalize_coords(LKP, FindLoc, trails_arr):
    # Repeat LKP for each simulation from trails_arr for easy matrix calculation
    LKP_arr = np.tile(LKP, (trails_arr.shape[0], 1))

    # Normalize points around the LKP location (0, 0)m
    trails_norm = trails_arr - LKP_arr
    FindLoc_norm = FindLoc - LKP

    return trails_norm, FindLoc_norm

def Plot_inliers(trails_norm, FindLoc_norm, Pden_threshold):
    # Defining the extent based on the Pden_threshold
    extent_x_min = FindLoc_norm[0] - Pden_threshold/2
    extent_x_max = FindLoc_norm[0] + Pden_threshold/2
    extent_y_min = FindLoc_norm[1] - Pden_threshold/2
    extent_y_max = FindLoc_norm[1] + Pden_threshold/2

    # Using numpy boolean mask to check which coordinates are inliers. This creates an array of Boolean terms 
    inlier_mask = (
        (trails_norm[:, 0] >= extent_x_min) &
        (trails_norm[:, 0] <= extent_x_max) &
        (trails_norm[:, 1] >= extent_y_min) &
        (trails_norm[:, 1] <= extent_y_max)
    )

    # Extract inliers and outliers
    inlier_coords = trails_norm[inlier_mask]        # Ouputs only the terms that the boolean mask says are True
    outlier_coords = trails_norm[~inlier_mask]      # Ouputs only the terms that the boolean mask says are False

    # Count number of inliers
    num_inliers = np.sum(inlier_mask)
    num_total_simulations = trails_arr.shape[0]

    # Print results of number of inliers relative to total.
    print(f"The Probability density of the simulation around the find location, within a box of {Pden_threshold}x{Pden_threshold}m is: ", num_inliers / num_total_simulations )
    print(f"\nThe number of inliers is {num_inliers}")

    # Plot the results
    plt.plot(outlier_coords[:, 0], outlier_coords[:, 1], 'ro')
    plt.plot(inlier_coords[:, 0], inlier_coords[:, 1], 'go')
    plt.plot(0, 0, 'bo')
    plt.plot(FindLoc_norm[0], FindLoc_norm[1], 'yo')
    plt.show()

    # Plotting zoomed in results
    plt.plot(outlier_coords[:, 0], outlier_coords[:, 1], 'ro')
    plt.plot(inlier_coords[:, 0], inlier_coords[:, 1], 'go')
    plt.plot(0, 0, 'bo')
    plt.plot(FindLoc_norm[0], FindLoc_norm[1], 'yo')
    
    plt.xlim(extent_x_min - 100, extent_x_max + 100)
    plt.ylim(extent_y_min - 100, extent_y_max + 100)

    plt.show()

def runprog(path, Pden_pix_res, do_plots):

    
    trails_arr = open_trails_csv(path[0])
    trail_norm, FindLoc_norm = Normalize_coords(path[1], FindLoc, trails_arr)

    for res in Pden_pix_res:

        BinVal = 25000 // res                     # Converting pixel size to bin value for histogram computation. 

        # Using the desired PDM resolution to visualize the inliers and outliers 
        Pden_threshold = res 
        if do_plots:
            None
            #Plot_inliers(trail_norm, FindLoc_norm, Pden_threshold)


        # Using Sava et. al's. method to calculate simulation performance.

        # generate an image with pixels so that each pixel is 5mx5m
        H, xedges, yedges = np.histogram2d(
            trail_norm[:, 0],  # all x-coords
            trail_norm[:, 1],  # all y coords
            bins=BinVal,                                # Does Sava et. al. use bins = 5000?
            range=[[-12500, 12500], [-12500, 12500]]    # values based on the values used by Sava et. al.
        )

        #transpos so that it works as an image
        H = H.T

        prob_map = H / H.sum() # if H.sum() > 0 else H     # Normalize histogram to sum up to 1. Each pixel will then equal the probability distribution for that area.

        # factorize the probability map to Sava's 5x5m = 25m^2 pixel requirement
        # Uniformly reduces each pixel value to be what each 5x5m pixel would have had.
        pix_factor = (res*res) / 25
        prob_map = prob_map / pix_factor

        #find_rc = xy_to_rowcol(FindLoc_norm[0], FindLoc_norm[1], extent, prob_map.shape)
        #R = mapscore(prob_map, find_rc, pix_factor)

        # find the area of inliers above a threshold of R=0.1

        print("For: ", path[0])
        InlierArea(prob_map, res, pix_factor)

        #print(f"The R-score for this simluation run with PDM pixel size {res}^2 is: {R}")

        if do_plots:
            # Plotting the histogram - probability distribution map.
            plt.figure(figsize=(20, 20))
            im = plt.imshow(H, origin="lower", extent=(-12500, 12500, -12500, 12500))
            #im2 = plt.imshow(prob_map, origin="lower", extent=(-12500, 12500, -12500, 12500))
            #plt.colorbar(im)
            plt.title("End points prabability map")
            plt.xlabel("X")
            plt.ylabel("Y")
            plt.show()

        return None



# Input variables:

PROJECT_ROOT = Path(__file__).parent
OUTPUT = PROJECT_ROOT / "output"

file_paths = [
        OUTPUT / "Plot_D_CFG_Jotunheimen_Hiker_1_10000_trails.csv",# np.array([144139.23, 6843390.05])),        
]

LKP = np.array([144139.23, 6843390.05])              # The last known position of the missing person before they went missing (a.k.a. IPP)
FindLoc = np.array ([274872.57, 6633866.46])         #  ([44862.99, 6468491.51])         # The find location of the mission person 

extent = -12500, 12500, -12500, 12500               # The extent of the map in m - used by Sava et. al.

Pden_pix_res = [100] #[250, 100, 50, 20, 10, 5]                                  # The pixel size of the Probability Density Map (PDM) (Xm x Ym)        

do_plots = True             # If True, plots are generated

# print("Running evaluation for: ", file_paths)

#for path in file_paths:
#    runprog(path, Pden_pix_res, do_plots)

#--------------------------------------------------------------------------------------------------------------------
# Old code
#--------------------------------------------------------------------------------------------------------------------

trails_norm = []
for path in file_paths:
    trails_arr = open_trails_csv(path)
    trail_norm, FindLoc_norm = Normalize_coords(LKP, FindLoc, trails_arr)

    trails_norm.append(trail_norm)

trails_norm = np.vstack(trails_norm)


print("Number of agents: ", trails_norm.shape[0])

for _, res in enumerate(Pden_pix_res):

    BinVal = 25000 // res                     # Converting pixel size to bin value for histogram computation. 

    # Using the desired PDM resolution to visualize the inliers and outliers 
    Pden_threshold = res 
    if do_plots:
        None
        #Plot_inliers(trails_norm, FindLoc_norm, Pden_threshold)


    # Using Sava et. al's. method to calculate simulation performance.

    # generate an image with pixels so that each pixel is 5mx5m
    H, xedges, yedges = np.histogram2d(
        trails_norm[:, 0],  # all x-coords
        trails_norm[:, 1],  # all y coords
        bins=BinVal,                                # Does Sava et. al. use bins = 5000?
        range=[[-12500, 12500], [-12500, 12500]]    # values based on the values used by Sava et. al.
    )

    #transpos so that it works as an image
    H = H.T

    prob_map = H / H.sum() # if H.sum() > 0 else H     # Normalize histogram to sum up to 1. Each pixel will then equal the probability distribution for that area.

    # factorize the probability map to Sava's 5x5m = 25m^2 pixel requirement
    # Uniformly reduces each pixel value to be what each 5x5m pixel would have had.
    pix_factor = (res*res) / 25
    prob_map = prob_map / pix_factor

    #find_rc = xy_to_rowcol(FindLoc_norm[0], FindLoc_norm[1], extent, prob_map.shape)
    #R = mapscore(prob_map, find_rc, pix_factor)

    # find the area of inliers above a threshold of R=0.1

    InlierArea(prob_map, res, pix_factor)

    #print(f"The R-score for this simluation run with PDM pixel size {res}^2 is: {R}")

    if do_plots:
        # Plotting the histogram - probability distribution map.
        plt.figure(figsize=(20, 20))
        im = plt.imshow(H, origin="lower", extent=(-12500, 12500, -12500, 12500))
        #im2 = plt.imshow(prob_map, origin="lower", extent=(-12500, 12500, -12500, 12500))
        #plt.colorbar(im)
        plt.scatter(0.0, 0.0, s=80, marker="o", edgecolor="black", facecolor="green", zorder=5)
        plt.title("End points prabability map")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.savefig("Result_Area_above_thresh_D_CFG_Jotunheimen_Hiker_1.pdf")
        plt.show()
        

plt.figure(figsize=(12, 12))
plt.plot(trails_norm[:, 0], trails_norm[:, 1], 'ro')
plt.plot(0, 0, 'bo')
plt.plot(FindLoc_norm[0], FindLoc_norm[1], 'yo')
plt.show()

# plt.plotting_UTM(CFG, plot_background, MapData.dtm_extent, CFG.start_UTM_x, CFG.start_UTM_y, heatmap, trails, plot_save_path=MapData.plot_save_path, color_bar=color_bar, autosize=autosize, save_plots=save_plots)
