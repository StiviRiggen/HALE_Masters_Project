import numpy as np

import utilities as utl

# --- Movement Models ---------------------------------------------------

def DirrectionTraveling(state, CFG, MapData):
    """Function to move the hiker in a constant bearing direction."""
    # time & distance per step
    dt = CFG.sim_res_sec  # seconds
    step_dist = state.speed * dt # meters

    # Update location using trigenometry.
    new_x = state.x + step_dist * np.cos(state.bearing) 
    new_y = state.y + step_dist * np.sin(state.bearing)

    state.movement = "DT"       # Save info on what movement model is used this step => DT = DirectionTravel

    bearing = state.bearing

    return bearing

def RandomWlak(state, CFG, MapData):
    """Function to move the hiker in a stochastic bearing direction."""
    # time & distance per step
    dt = CFG.sim_res_sec  # seconds
    step_dist = state.speed * dt # meters

    bearing = state.bearing

    if not state.near_road:   # only add some randomness if not on road
        bearing += np.random.normal(0, np.deg2rad(CFG.bearing_jitter_deg))
        bearing %= 2*np.pi

    state.movement = "RW"       # Save info on what movement model is used this step => RW = RandomWalk

    return bearing

def ViewEnhancing(state, CFG, MapData):
    # get height at state
    h0 = utl.height_at_utm(state.x, state.y, MapData)
    highest_h = h0
    highest_bearing = state.bearing
    dh = 0

    step_dist = state.speed * CFG.sim_res_sec

    for _try in range(18):  # try every 10 degrees in both directions
            test_bearing = (state.bearing + np.deg2rad(_try * 10)) % (2 * np.pi)
            new_x = state.x + step_dist * np.cos(test_bearing) 
            new_y = state.y + step_dist * np.sin(test_bearing)

            check_height = utl.height_at_utm(new_x, new_y, MapData)

            if check_height > highest_h:
                highest_h = check_height
                highest_bearing = test_bearing
                dh = highest_h - h0
            
            test_bearing = (state.bearing - np.deg2rad(_try * 18)) % (2 * np.pi)
            new_x = state.x + step_dist * np.cos(test_bearing) 
            new_y = state.y + step_dist * np.sin(test_bearing)

            check_height = utl.height_at_utm(new_x, new_y, MapData)

            if check_height > highest_h:
                highest_h = check_height
                highest_bearing = test_bearing
                dh = highest_h - h0

            
    if dh < 2:
        state.movement = "VE_top"   # Marks that the agent has reached a local maxima elevation. This will initiate a change in strategy.
    else:
        state.movement = "VE"
    
    return highest_bearing


def StayingPut(state, CFG, Mapdata):

    state.movement = "SP"

    return state.bearing


def BackTracking(state, CFG, Mapdata):

    new_bearing = state.bearing - np.pi

    if new_bearing < 0:
        new_bearing = new_bearing + 2 * np.pi

    state.movement = "BT"

    return new_bearing
