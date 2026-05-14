import numpy as np
from utilities import height_at_utm, is_water, DDA, rng

# --- Blockers -----------------------------------------------

def fell_off_map(state, CFG, cand_x, cand_y, MapData):
    """Blocker to check if the candidate position is off the map."""

    # Check if the candidate position is out of bounds.
    
    if cand_x < MapData.dtm_extent[0] or cand_x > MapData.dtm_extent[1] or cand_y < MapData.dtm_extent[2] or cand_y > MapData.dtm_extent[3]:
        blocked = True
        blocker_name = "Terminated_out_of_bounds"
        return blocked, blocker_name  # Block if out of bounds
    else:
        blocked = False
        blocker_name = "NIL"
        return blocked, blocker_name

def terrain_blocker(state, CFG, cand_x, cand_y, MapData):
    # Check if the candidate position is on terrain that is too steep
    if state.near_road:
        blocked = False
        blocker_name = "NIL"
        return blocked, blocker_name

    h0 = height_at_utm(state.x, state.y, MapData)
    h1 = height_at_utm(cand_x, cand_y, MapData)
    if np.isnan(h1) or np.isnan(h0):
        blocked = True
        blocker_name = "Terminated_out_of_bounds"
        return blocked, blocker_name  # Block if out of bounds
    dz = h1 - h0        # Delta height
    step_dist = state.speed * CFG.sim_res_sec
    max_grad = CFG.slope_max_climb_deg * np.pi / 180   # Convert to rad - max uphill slope to accept
    max_dz = np.tan(max_grad) * step_dist
    min_grad = CFG.slope_max_fall_deg * np.pi / 180   # Convert to rad - terminal downhill slope
    min_dz = np.tan(min_grad) * step_dist
    if dz > max_dz:
        blocked = True
        blocker_name = "pos_steep"
        return blocked, blocker_name  # Block if too steep up hill
    elif dz < min_dz:
        blocked = True
        blocker_name = "neg_steep"
        return blocked, blocker_name  # Block if too steep down hill
    else:
        blocked = False
        blocker_name = "NIL"
        return blocked, blocker_name

def water_blocker(state, CFG, cand_x, cand_y, MapData):
    
    if state.near_road:
        blocked = False
        blocker_name = "NIL"
        return blocked, blocker_name  # If on road, water blocker does not apply - allowing agent to cross bridges.
    
    # Check if the candidate position is on water
    water_check = is_water(cand_x, cand_y, MapData)
    if water_check:
        blocked = True
        blocker_name = "water"
        return blocked, blocker_name
    else:
        blocked = False
        blocker_name = "NIL"
        return blocked, blocker_name
    
def water_blocker_dda(state, CFG, cand_x, cand_y, MapData):
    # If on road, water blocker does not apply - allowing agent to cross bridges.
    if state.near_road:
        blocked = False
        blocker_name = "NIL"
        return blocked, blocker_name  
    
    # Check if the candidate position is on water
    dda_points = DDA(MapData.dtm_tfm, state.x, state.y, cand_x, cand_y, dda_resolution=3)       # DDA resolution in m. Lower res = faster simulation time. Relative to road buffer distance.
    for (r, c) in dda_points:

        if r < 0 or c < 0 or r >= MapData.wm_arr.shape[0] or c >= MapData.wm_arr.shape[1]:
            water_check = True # Count out of bounds as water to avoid "falling off the map" error in the DDA function.
            break

        check = MapData.wm_arr[r, c]
        if check == 1:
            water_check = True
            break
        else:
            water_check = False
    if water_check:
        blocked = True
        blocker_name = "water"
        return blocked, blocker_name
    else:
        blocked = False
        blocker_name = "NIL"
        return blocked, blocker_name

def waiting_blocker(state, CFG, cand_x, cand_y, MapData):

    def waiting_func(CFG, steps_left):
        """Function to determine if the hiker waits at their current location this step."""
        if rng.uniform(0, 1) >= CFG.waiting_prob:  # 10% chance to wait this step
            return 0

        wait_sec = rng.normal(loc=CFG.waiting_mean_sec, scale=CFG.waiting_std_dev_sec)

        min_sec = CFG.sim_res_sec
        max_sec = steps_left * CFG.sim_res_sec
        wait_sec = np.clip(wait_sec, min_sec, max_sec)

        wait_steps = int(np.ceil(wait_sec / CFG.sim_res_sec))

        return max(1, min(wait_steps, steps_left))  # Ensure at least 1 step if waiting and not more than steps left
            
    # Check if hiker is waiting this step
    if state.waiting_steps_left == 0:
        steps_left = state.sim_total_steps - state.sim_step
        waiting_steps = waiting_func(CFG, steps_left)
        state.waiting_steps_left = waiting_steps

    if state.waiting_steps_left > 0:
        state.waiting_steps_left -= 1
        blocked = True
        blocker_name = "waiting"
        return blocked, blocker_name
    else:
        blocked = False
        blocker_name = "NIL"
        return blocked, blocker_name
    
def StayingPut_Blocker(state, CFG, cand_x, cand_y, MapData):
    if state.movement == "SP":
        blocked = True
        blocker_name = "waiting"
        return blocked, blocker_name
    else:
        blocked = False
        blocker_name = "NIL"
        return blocked, blocker_name



# --- Policies ----------------------------------------------------
# Policies decide what happens when the hiker is blocked. They function in hierarchical order of most to least severe i.o.w. least to most likely.
def terminate_policy(blocker_name, CFG):
    """Policy to terminate the simulation when blocked."""
    if blocker_name == "pos_steep":
        prob = rng.uniform(0, 1)
        if prob < CFG.pos_terminate_prob:
            #print("I fell up a cliff!")
            return "terminate", None
    elif blocker_name == "neg_steep":
        prob = rng.uniform(0, 1)
        if prob < CFG.neg_terminate_prob:
            #print("I fell down a cliff!")
            return "terminate", None
    elif blocker_name == "water":
        prob = rng.uniform(0, 1)
        if prob < CFG.water_terminate_prob:
            #print("I'm drowning!")
            return "terminate", None
    elif blocker_name == "Terminated_out_of_bounds":
        return "Terminated_out_of_bounds", None
    return None, None

def backtrack_policy(blocker_name, CFG):
    """Policy to choose a reverse bearing when blocked."""
    if blocker_name == "pos_steep":
        prob = rng.uniform(0, 1)
        if prob < CFG.backtrack_prob:
            return "backtrack", None
    elif blocker_name == "neg_steep":
        prob = rng.uniform(0, 1)
        if prob < CFG.backtrack_prob:
            return "backtrack", None
    return None, None

def new_bearing_policy(blocker_name, CFG):
    """Policy to choose a new random bearing when blocked."""
    if blocker_name == "pos_steep":
        return "new_bearing", None
    elif blocker_name == "neg_steep":
        return "new_bearing", None
    elif blocker_name == "water":
        #print("I'm changing direction to avoid water!")
        return "new_bearing", None
    return None, None