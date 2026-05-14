import numpy as np
from utilities import height_at_utm, check_near_road, DDA
from rasterio.transform import rowcol

# --- Speed Modifiers ----------------------------------------------------

#TODO: Add a speed modifier that takes into account fatigue over time/distance travelled. What is a good fatigue model?

def tobler_eq(state, CFG, cand_x, cand_y, MapData):
    """Function to modify the hiker's speed based on Tobler's hiking equation.
        Uses height at current location and height at candidate location to determine the gradient of the terrain.
    """
    dt = CFG.sim_res_sec  # seconds
    step_dist = state.speed * dt # meters
    h0 = height_at_utm(state.x, state.y, MapData)
    h1 = height_at_utm(cand_x, cand_y, MapData)
    if np.isnan(h1) or np.isnan(h0):
        speed_factor = 1
        return  speed_factor # No change if out of bounds
    dz = h1 - h0        # Delta height
    # Tobler's eq.
    s = dz / step_dist # slope ratio
    new_speed = CFG.max_speed * np.exp(-3.5 * np.abs(s + 0.05)) # new speed in m/s. (km/h reduced to 4.8 km/h for walking i terrain)
    speed_factor = new_speed / state.speed
    #TODO: Tobler eq can sometimes produce a speed factor that is up to 2.5, is this correct?
    return speed_factor # return speed increase/decrease factor

def tobler_DDA(state, CFG, cand_x, cand_y, MapData):
    """Function to modify the hiker's speed based on Tobler's hiking equation.
        Uses DDA analysis to rasterize the path between the current location an the candidate location.
        It finds the steepest gradient found along the path and returns the speed factor calculated by the Tobler equation and the gradient."""
    
    if cand_x < MapData.dtm_extent[0] or cand_x > MapData.dtm_extent[1] or cand_y < MapData.dtm_extent[2] or cand_y > MapData.dtm_extent[3]:
        return 1 # No speed factor added if next step will be out of bounds. This is to avoid DDA errors when exiting the extent of the map.

    dt = CFG.sim_res_sec  # seconds
    step_dist = state.speed * dt # meters
    dda_points = DDA(MapData.dtm_tfm, state.x, state.y, cand_x, cand_y, dda_resolution=5)      # Retreives all rows and colomns from the dtm raster that the hikers path will cross.
    dda_points_heights = []
    for (r, c) in dda_points:
        if r < 0 or c < 0 or r >= MapData.dtm_arr.shape[0] or c >= MapData.dtm_arr.shape[1]:
            dda_points_heights.append(np.nan)
        else:
            dda_points_heights.append(MapData.dtm_arr[r, c])
    dda_points_dz = []
    h0 = dda_points_heights[0]
    dz_sum = 0
    for i in range(len(dda_points_heights)):
        dz = dda_points_heights[i] - h0
        dda_points_dz.append(dz)
        dz_sum += dz
    dz = dz_sum/len(dda_points_heights) # Find the average dz accross the path
    #dz = max(dda_points_dz, key=abs)   # Find the maximum dz accross the path
    # Tobler's eq.
    s = dz / step_dist # slope ratio
    new_speed = CFG.max_speed * np.exp(-3.5 * np.abs(s + 0.05)) # Max walking speed in terrain
    speed_factor = new_speed / state.speed
    #rad = np.arctan(s)
    #deg = np.rad2deg(rad)
    #print(f"Tobler speed: {new_speed} with a slope of {deg} deg from a dz of {dz} and step distance of {step_dist} giving a speed factor of {speed_factor}")
    return speed_factor # return speed increase/decrease factor

def on_road(state, CFG, cand_x, cand_y, MapData):
    """Function to increase speed if on road."""
    road_check = check_near_road(cand_x, cand_y, MapData)
    if road_check:
        speed_factor = CFG.on_road_speed_factor
        return speed_factor # return speed increase/decrease factor
    else:
        speed_factor = 1 # No increase in speed.
        return speed_factor
    
def terrain_type(state, CFG, cand_x, cand_y, MapData):
    """Function to modify the hiker's speed based on terrain type.
        Uses the different terrain masks to determine if the candidate location is in a certain terrain type and modifies speed accordingly.
    """
    # Check if near agent is in on road, if so return without speed modification. Terrain type has no effect if agent is on a road.
    if state.near_road:
        return 1
    
    # Check is agent is in forest, if so return speed modification factor.
    r, c = rowcol(MapData.dtm_tfm, state.x, state.y, op=round)

    if MapData.forest_arr[r, c] == 1:
        return CFG.forrest_speed_factor

    # Check is agent is in marsh, if so return speed modification factor.
    if MapData.marsh_arr[r, c] == 1:
        return CFG.marsh_speed_factor

    # Check is agent is in developed area, if so return speed modification factor.
    if MapData.developed_arr[r, c] == 1:
        return CFG.developed_speed_factor

    # Check is agent is in open area, if so return speed modification factor.
    if MapData.open_area_arr[r, c] == 1:
        return CFG.open_area_speed_factor

    return 1