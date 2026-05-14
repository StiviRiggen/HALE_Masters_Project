import numpy as np
from rasterio.transform import rowcol
import datetime

import movement_models as mm
import direction_modifiers as dm
import speed_modifiers as sm
import blockers_and_policies as bp

import plotting as plt
import config as cfg
import utilities as utl
import pandas as pd


# --- MAIN UPDATE FUNCTION ----------------------------------------------------

def Update(state, MapData, CFG, 
           movement_models, movement_models_lookup, speed_modifiers, dir_modifiers, blockers, block_policies
    ):
    """
    Function the Update function:
    ------------------------------------
    Step 1: Apply movement model to suggest new position
    While: checking if any modifiers or blockers apply
        Step 2: Apply direction modifiers to adjust bearing if relevant
        Step 3: Apply speed modifiers to adjust speed if relevant
        Step 4: Apply blockers to check if movement is valid
        Step 5: If blocked, use block_policy to determine new action
            5.1 If terminate, end simulation
            5.2 If new bearing, suggest a new bearing and re-try from Step 2
    Step 6: If not blocked, update hiker state with new position, and bearing
    ------------------------------------
    """
    attempts = 0
    
    # Choose a movement model based on the probabilities in the CFG, inertia and if the last step was BackTracking
    if utl.rng.uniform(0, 1) > CFG.movement_inertia or state.movement == "BT" or state.movement == "VE_top": # If the last step was BackTracking we don't want to backtrack again. Same with view enhancing when we reach a local maxima.
        movement = np.random.choice(movement_models, p=CFG.movement_prob)
        bearing = movement(state, CFG, MapData)
    else:
        movement = movement_models_lookup[state.movement]
        bearing = movement(state, CFG, MapData)

    while attempts < CFG.bearing_k:
        attempts += 1

        # Reset values:
        state.speed = CFG.max_speed      # Reset to standard speed each step which is then modified by speed modifiers

        # Apply movement model and suggest new position
        # cand_x, cand_y, new_bearing, step_dist = movement_model(state)

        # Propose candidate position with bearing and standard step distance
        step_dist = state.speed * CFG.sim_res_sec
        cand_x = state.x + step_dist * np.cos(bearing)
        cand_y = state.y + step_dist * np.sin(bearing)

        # Apply direction modifiers WIP
        for modifier in dir_modifiers:
            bearing = modifier(state, CFG, cand_x, cand_y, MapData, step_dist, bearing)

        # Apply speed modifiers
        speed = CFG.max_speed
        for modifier in speed_modifiers:
            speed *= modifier(state, CFG, cand_x, cand_y, MapData)
        step = speed * CFG.sim_res_sec
        cand_x = state.x + step * np.cos(bearing)
        cand_y = state.y + step * np.sin(bearing)

        blocked = False
        terminated = False
        terminated_OoB = False
        blocker_name = None
        need_retry = False
        waiting = False

        # Apply blockers
        for blocker in blockers:
            blocked, blocker_name = blocker(state, CFG, cand_x, cand_y, MapData) # returns [blocker_name, blocked=True/False]
            if blocked:
                if blocker_name == "waiting":
                    waiting = True
                    break  # No policies for waiting, just break to handle waiting
                else:
                    waiting = False
                for policy in block_policies:
                    action, value = policy(blocker_name, CFG)
                    if action == "terminate":
                        terminated = True
                        break  # Break out of policy loop to terminate
                    elif action == "Terminated_out_of_bounds":
                        terminated_OoB == True
                        break
                    elif action == "new_bearing":   # Pick a new bearing and try again
                        bearing = float(value) if value is not None else np.random.uniform(0, 2*np.pi)  # pick a new random direction
                        need_retry = True
                        break  # Break out of policy loop to try new bearing
                    elif action == "backtrack":
                        # print("This is the wrong way, I'm going back!")
                        bearing = (state.bearing + np.pi) % (2*np.pi)
                        need_retry = True
                        break  # Break out of policy loop to try new bearing
    
                break  # Break out of blocker loop to re-try or terminate


        # Add a final Out of bounds checker:
        bounds_check = utl.height_at_utm(cand_x, cand_y, MapData)
        if np.isnan(bounds_check):
        # starting on NoData → stop
            terminated_OoB = True
            

        if terminated:
            return cfg.HikerState(
                    x=cand_x,
                    y=cand_y,
                    bearing=bearing,
                    speed=state.speed,
                    terminated=True
                    #TODO: Add termination_cause = blocker_name later?
                )
        
        if terminated_OoB:
            return cfg.HikerState(
                    x=cand_x,
                    y=cand_y,
                    bearing=bearing,
                    speed=state.speed,
                    terminated=True,
                    terminated_OoB=True
                    #TODO: Add termination_cause = blocker_name later?
                )

        if need_retry:
            continue  # Try a new bearing

        # candidate position blocked due to waiting
        if waiting:
            return cfg.HikerState(
                x=state.x,
                y=state.y,
                bearing=bearing,
                speed=state.speed,
                sim_step=state.sim_step,
                sim_total_steps=state.sim_total_steps,
                waiting_steps_left=state.waiting_steps_left,
                near_road=state.near_road,
                movement=state.movement
            )
        
        #Check if candidate position is within bounds

        # candidate position accepted
        return cfg.HikerState(
            x=cand_x,
            y=cand_y,
            bearing=bearing,
            speed=state.speed,
            sim_step=state.sim_step,
            sim_total_steps=state.sim_total_steps,
            near_road=state.near_road,
            movement=state.movement

        )

        
        # If the candidate location is neither accepted nor terminated, the loop continues to try a new bearing.
    
    # Too many retries - no movement this step.
    # print("Too many blocked attempts, staying in place this step.")
    return cfg.HikerState(
                x=state.x,
                y=state.y,
                bearing=bearing,
                speed=state.speed,
                sim_step=state.sim_step,
                sim_total_steps=state.sim_total_steps,
            )


def sim_runner(
        CFG, MapData, 
        #movement_model, dir_modifiers, speed_modifiers, blockers, block_policies,
        do_plots, save_csv, heatmap, save_plots, color_bar, autosize, plot_background, normalize_plot
    ):
    """
    Function that performs the overall simulation runs while the Update function above handles actions at each step.
    """

    # Look-up dictionaries to convert from config strings to actual functions

    movement_models_lookup = {
        "DT": mm.DirrectionTraveling,
        "RW": mm.RandomWlak,
        "VE": mm.ViewEnhancing,
        "SP": mm.StayingPut,
        "BT": mm.BackTracking
    }
    dir_modifiers_lookup = {
        "follow_road_dda": dm.follow_road_dda
    }
    speed_modifiers_lookup = {
        "tobler_DDA": sm.tobler_DDA,
        "on_road": sm.on_road,
        "terrain_type": sm.terrain_type
    }
    blockers_lookup = {
        "fell_off_map": bp.fell_off_map,
        "waiting_blocker": bp.waiting_blocker,
        "water_blocker_dda": bp.water_blocker_dda,
        "terrain_blocker": bp.terrain_blocker,
        "StayingPut_Blocker": bp.StayingPut_Blocker
    }
    block_policies_lookup = {
        "terminate_policy": bp.terminate_policy,
        "backtrack_policy": bp.backtrack_policy,
        "new_bearing_policy": bp.new_bearing_policy
    }

    # Convert config strings to actual functions
    movement_models = [movement_models_lookup[name] for name in CFG.movement_models]
    dir_modifiers = [dir_modifiers_lookup[name] for name in CFG.dir_modifiers]
    speed_modifiers = [speed_modifiers_lookup[name] for name in CFG.speed_modifiers]
    blockers = [blockers_lookup[name] for name in CFG.blockers]
    block_policies = [block_policies_lookup[name] for name in CFG.block_policies]
    
    trails = []  # To store all trails from multiple simulations
    extra_endpoints = [] # To store extra endpoints for plotting with trails

    # Check if starting point is valid
    valid_start = True

    # 1. Within DTM?
    h0 = utl.height_at_utm(CFG.LKP[0], CFG.LKP[1], MapData)
    if np.isnan(h0):
    # starting on NoData → stop
        print("starting point is outside of valid DTM")
        valid_start = False

    # 2. In water?
    init_water_check = utl.is_water(CFG.LKP[0], CFG.LKP[1], MapData)
    if init_water_check is True:
        print("Starting point in water! Hiker has drowned emediatly!")
        valid_start = False

    # Initializing timing variables
    time_updater = 1
    delta_time_list = []
    time_gone = datetime.datetime.now() - datetime.datetime.now()

    for sim in range(CFG.sim_num):
        time_updater -= 1
        start_time = datetime.datetime.now()

        # Don't run simulations if starting point is invalid
        if valid_start is False:
            break

        steps = int((CFG.hours_missing * 3600) / CFG.sim_res_sec)

        # Initializing the hiker state with parameters from config.py and random bearing.
        state = cfg.HikerState(
            x=CFG.LKP[0],
            y=CFG.LKP[1],
            bearing=np.random.uniform(0,2*np.pi), # initial bearing in rad.
            speed=CFG.max_speed,
            sim_step=0,
            sim_total_steps=steps,
            near_road=False,
            movement="DT"
        )

        if CFG.init_bearing is not None:
            state.bearing = CFG.init_bearing

        trail = []
        trail.append((state.x, state.y))   # Store initial position
        extra_endpoint = []                # Initiate the storage of extra endpoints
        for step in range(steps):
            state = Update(
                state,
                MapData,
                CFG,
                movement_models,
                movement_models_lookup,
                speed_modifiers,
                dir_modifiers,
                blockers,
                block_policies,
            )

            # For every 30 steps, generate a new end point (every 30 min)
            step_counter = step + 1
            #--------
            if step_counter % 30 == 0:                      # Counts from one to avoide generating points at the LKP.
                #extra_endpoint.append((state.x, state.y))
                None
            #--------

            trail.append((state.x, state.y))
            state.sim_step = step+1

            if state.terminated: break

        #--------
        if state.terminated_OoB:
            # When the agent leaves the bounds of the search area the path and final endpoint is removed but the extra endpoints are kept as these are places the LP could have stoped.
            if heatmap:
                # trails.append(np.asarray(trail[-1], dtype=float))
                for i, _ in enumerate(extra_endpoint):
                    trails.append(np.asarray(extra_endpoint[i], dtype=float))
            else:
                trails.append(trail)
                #extra_endpoints.append(extra_endpoint)    # uncomment to save extra endpoints when plotting trails.
                None
        else:
            if heatmap:
                trails.append(np.asarray(trail[-1], dtype=float))
                for i, _ in enumerate(extra_endpoint):
                    trails.append(np.asarray(extra_endpoint[i], dtype=float))
            else:
                trails.append(trail)
                #extra_endpoints.append(extra_endpoint)    # uncomment to save extra endpoints when plotting trails.
        #--------

        # trails.append(np.asarray(trail[-1], dtype=float) if heatmap else trail) # old version of code.

        ### Main timing function ###
        end_time = datetime.datetime.now()
        time_delta = end_time - start_time
        delta_time_list.append(time_delta)
        sims_left = CFG.sim_num - sim
        time_gone += time_delta
        # Time display only updates every 20 simulations for smoother viewing.
        if time_updater == 0:
            average_sim_time = np.mean(delta_time_list)
            time_remaining = average_sim_time * sims_left
            total_time = time_remaining + time_gone

            time_remaining_n = utl.format_td(time_remaining)
            total_time_n = utl.format_td(total_time)

            time_updater = 500
        # Placing a cap on total number of values in list.
        if len(delta_time_list) >= 500:
            delta_time_list = delta_time_list[499:]
        # print(f"\r  Simulations completed: {sim}/{CFG.sim_num} - Time remaining: {time_remaining_n}/{total_time_n}", end="", flush=True)
        if time_updater == 500:
            print(f"\n{CFG.config_name} Simulations completed: {sim}/{CFG.sim_num} - Time remaining: {time_remaining_n}/{total_time_n}", end="", flush=True)

    # Save trails data to CSV for later analysis or plotting
    if save_csv:
        all_trails = []
        if heatmap:
            for i, (x,y) in enumerate(trails):
                all_trails.append({'sim': i, 'x': x, 'y': y})
        else:
            for i, trail in enumerate(trails):
                #print(trails)
                for step, (x, y) in enumerate(trail):
                    all_trails.append({'sim': i, 'step': step, 'x': x, 'y': y})
        df = pd.DataFrame(all_trails)
        df.to_csv(f"{MapData.plot_save_path}{CFG.config_name}_{CFG.sim_num}_trails.csv", index=False)
        print(f"\n.CSV file saved as: {MapData.plot_save_path}{CFG.config_name}_{CFG.sim_num}_trails.csv")

    # Plotting function (Backgrounds: dtm_arr, wm_arr, buff_roads_arr)
    if do_plots:
        plt.plotting_UTM(CFG, plot_background, MapData.dtm_extent, CFG.LKP[0], CFG.LKP[1], heatmap, trails, extra_endpoints, plot_save_path=MapData.plot_save_path, color_bar=color_bar, autosize=autosize, save_plots=save_plots, normalize_plot=normalize_plot)
    
    


# TODO: Add function to save trails to .txt file for later plotting of multiple trails - best way to solv this?    
#    with open(f"{MapData.plot_save_path}{CFG.config_name}_trails.txt", "w") as f:
#        f.write(str(trails))