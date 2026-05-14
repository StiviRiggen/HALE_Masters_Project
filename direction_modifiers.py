import numpy as np
from utilities import check_near_road, check_near_road_near, DDA, rng

# --- Direction Modifiers ------------------------------------------------

#TODO: Add a direction modifier that takes into account the gradient of the terrain for agents stratigies (elevation gain/loss preferences).
     # Alternatively, could be added following linear terrain features such as ridges or valleys.
#TODO: Add a distance view fucntion? Easily doable?
#TODO: Add a backtracking modifier? Maybe based on agents stratigies.
#TODO: Add a water shed modifier?

def follow_road(state, CFG, cand_x, cand_y, MapData, step_dist, bearing):
    """Function to move the hiker along the road when near and following road.
    Starting from the current bearing check bearings in both directions to find the road direction.
    If no road found within 180 degrees, return original location and set following_road to False."""
    road_check = check_near_road(state.x, state.y, MapData)
    # Check follow road probability
    following_road = False
    if road_check and rng.uniform(0, 1) < CFG.follow_road_prob:
        #print("\n I'm following a road!")
        for _try in range(36):  # try every 5 degrees in both directions
            test_bearing = (bearing + np.deg2rad(_try * 5)) % (2 * np.pi)
            new_x = state.x + step_dist * np.cos(test_bearing) 
            new_y = state.y + step_dist * np.sin(test_bearing)

            #TODO: Will this method always turn left at a junction?

            road_check = check_near_road(new_x, new_y, MapData)
            if road_check:
                #print("I'm going right")
                return test_bearing

            test_bearing = (bearing - np.deg2rad(_try * 5)) % (2 * np.pi)
            new_x = state.x + step_dist * np.cos(test_bearing) 
            new_y = state.y + step_dist * np.sin(test_bearing)

            road_check = check_near_road(new_x, new_y, MapData)
            if road_check:
                #print("I'm going left")
                return test_bearing

    return bearing

def follow_road_dda(state, CFG, cand_x, cand_y, MapData, step_dist, bearing):
    """Function to move the hiker along the road when near and following road.
    Starting from the current bearing check bearings in both directions to find the road direction.
    If no road found within 180 degrees, return original location and set following_road to False."""

    # Check if candidate position leaves map bounds - if so, return original bearing to avoid "falling off the map" error in the DDA function.
    if cand_x < MapData.dtm_extent[0] or cand_x > MapData.dtm_extent[1] or cand_y < MapData.dtm_extent[2] or cand_y > MapData.dtm_extent[3]:
        return bearing
    if state.x < MapData.dtm_extent[0] or state.x > MapData.dtm_extent[1] or state.y < MapData.dtm_extent[2] or state.y > MapData.dtm_extent[3]:
        return bearing
    
    dda_points = DDA(MapData.dtm_tfm, state.x, state.y, cand_x, cand_y, dda_resolution=10)       # DDA resolution in m. Lower res = faster simulation time. Relative to road buffer distance.
    for (r, c) in dda_points:
        # TODO: If hours missing is increased too much this check will have a "fall off the map error". Can be solved with the following code, but verry slow.
        # TODO: Better to create a better "fall off the map" checker.
        if r < 0 or c < 0 or r >= MapData.roads_arr.shape[0] or c >= MapData.roads_arr.shape[1]:
            road_check = False
            break
        check = MapData.buff_roads_arr[r, c]
        if check == 1:
            road_check = True
            state.near_road = True
            break
        else:
            road_check = False
            state.near_road = False
    # Check follow road probability
    if road_check and rng.uniform(0, 1) < CFG.follow_road_prob:
        for _try in range(180):  # try every 5 degrees in both directions
            test_bearing = (bearing + np.deg2rad(_try)) % (2 * np.pi)
            new_x = state.x + step_dist * np.cos(test_bearing) 
            new_y = state.y + step_dist * np.sin(test_bearing)

            #TODO: Will this method always turn left at a junction?

            road_check = check_near_road_near(new_x, new_y, MapData)
            if road_check:
                #print("I'm going right")
                return test_bearing

            test_bearing = (bearing - np.deg2rad(_try)) % (2 * np.pi)
            new_x = state.x + step_dist * np.cos(test_bearing) 
            new_y = state.y + step_dist * np.sin(test_bearing)

            road_check = check_near_road_near(new_x, new_y, MapData)
            if road_check:
                #print("I'm going left")
                return test_bearing

    return bearing