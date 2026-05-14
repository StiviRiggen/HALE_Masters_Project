import numpy as np
from dataclasses import dataclass, field

@dataclass
class CFG:
    """Provides classes of configuration parameters for running multiple simulations"""

    config_name: str = "Hiker_CFG"
    
    sim_num: int = 10000                     # Number of simulations to run
    sim_res_sec: int = 60                   # Time resolution for each step in simulation in seconds

    # LKP location:
    LKP: tuple = (117926.26, 6914652.23)
    FindLoc: tuple = (None, None)         #  ([44862.99, 6468491.51])         # The find location of the mission person

    #start_UTM_x: float = 45341.53-50            # UTM coordinates EAST axis
    #start_UTM_y: float = 6468022.89-50        # UTM coordinates NORTH axis
        
    init_bearing: float = None                          # Can input and inital bearing that the lost person is expected to have moved from LKP. (in RADIANS)

    # Simulation modifiers and policies:
    """
    LIST OF ALL FUNCTIONS:

    Using movement model to add re-orientation strategies:
    Random_Walk(stochastic bearing), Route_travel(constant bearing), Direction_sampling(constant w/ backtracking), Staying_put(Wainting function), View_enhancing (increase_elevation), Backtracking (move back X steps in the track?)

    Note! The SP movement requires the "StayingPut_Blocker" to function.

    movement_model (Choose only one)    = "RW", "DT", "VE", "SP", "BT" 
    dir_modifiers                       = dm.follow_road_dda,
    speed_modifiers                     = sm.tobler_DDA,            sm.on_road,             sm.terrain_type
    blockers                            = bp.fell_off_map,          bp.waiting_blocker or "StayingPut_blocker",     bp.water_blocker_dda,       bp.terrain_blocker                                        
    block_policies                      = bp.terminate_policy,      bp.backtrack_policy,    bp.new_bearing_policy 
    """

    movement_prob: list[float]  = field(default_factory=lambda: [0.6, 0.3, 0.05, 0.05])         # Provides the probabilities that each movement model will be chosen this step. NB: Order of the probs must mach the order of the movement models.
    movement_inertia: float     = 0.8       # This is the probability that the movement model will stay the same this step.

    movement_models: list[str]  = field(default_factory=lambda: ["DT", "RW", "VE", "BT"])       
    dir_modifiers: list[str]    = field(default_factory=lambda: ["follow_road_dda"])
    speed_modifiers: list[str]  = field(default_factory=lambda: ["tobler_DDA", "on_road", "terrain_type"])
    blockers: list[str]         = field(default_factory=lambda: ["fell_off_map", "StayingPut_Blocker", "water_blocker_dda", "terrain_blocker"]) # Can use "waiting_blocker" instead of StayingPut_Blocker for more fine tuned controll over staying put.
    block_policies: list[str]   = field(default_factory=lambda: ["terminate_policy", "backtrack_policy", "new_bearing_policy"])

    # Hiker movement parameters:
    hours_missing: float = 8                # Time since hiker was at IPP in hours (0.0833 hours = 5 minutes)
    max_speed: float = 1                    # Hikers maximum walking speed (m/s) on flat rough terrain. Number derived from research and assumptions - see Lab notes.
    bearing_k: int = 50                     # Bearings tested per step
    bearing_jitter_deg: int = 5             # Standard deviation of bearing changes per step

    # Hiker waiting_blocker parameters
    waiting_prob: float = 0.1               # Probability of hiker starting to wait at each step - Only used with the "Waiting Blocker"
    waiting_mean_sec: int = 600             # Mean number of seconds to wait when waiting (600 sec = 10 minutes)
    waiting_std_dev_sec: int = 600          # Standard deviation of seconds to wait when waiting

    # Hiker terrain movement characteristics
    slope_max_climb_deg: int = 31           # Maximum climbing slope - Hiker will pick a new bearing (TTCSM defines cliff as any slope > 31 degrees)
    slope_max_fall_deg: int = -31           # Maximum dicsent - Hiker will fall and stop. #TODO: Make more realistic such as a probability of falling
    backtrack_prob: float = 0.5             # Probability of backtracking when encountering steep slope

    ## Positive slope encounter policies
    #pos_new_bearing_prob: float = 0.9       # Probability of picking a new bearing when encountering steep slope
    pos_terminate_prob: float = 0.1         # Probability of terminating when encountering steep slope

    ## Negative slope encounter policies
    #neg_new_bearing_prob: float = 0.8       # Probability of picking a new bearing when encountering steep slope
    neg_terminate_prob: float = 0.2         # Probability of terminating when encountering steep slope
    
    # Road movement characteristics
    follow_road_prob: float = 0.8           # 100% probability of following road if on a road
    on_road_speed_factor: float = 1.25      # 25% walking speed increase when walking on path or road.

    # Water movement characteristics
    water_terminate_prob: float = 0.01      # 1% probability of terminating ("Drowning") With each step that encounters water

    # Speed modifiers:
    forrest_speed_factor: float = 0.5        # Speed factor when moving through forested area
    marsh_speed_factor: float = 0.3          # Speed factor when moving through marshy area
    developed_speed_factor: float = 1.0      # Speed factor when moving through developed
    open_area_speed_factor: float = 1.0      # Speed factor when moving through open area


@dataclass
class HikerState:
    """State of the hiker at a given time step."""
    x: float
    y: float
    bearing: float      # radians
    speed: float        # m/s

    """background states"""
    sim_step: int = 0
    sim_total_steps: int = 0
    
    waiting_steps_left: int = 0

    movement: str = "DT"         # Save the movement model used to have some memory (Inertia as Nuguyen calles it)

    terminated: bool = False
    terminated_OoB: bool = False  # Indicates that simulations is terminated due to the agent leaving the map coverage.        
    near_road: bool = False        
    
@dataclass
class MapData:
    """Provides "look-ups" for map and mask information."""
    dtm_arr: np.ndarray
    dtm_tfm: np.ndarray
    dtm_extent: np.ndarray
    wm_arr: np.ndarray
    wm_tfm: np.ndarray
    buff_roads_arr: np.ndarray
    buff_roads_tfm: np.ndarray
    roads_arr: np.ndarray
    roads_tfm: np.ndarray
    forest_arr: np.ndarray
    forest_tfm: np.ndarray
    marsh_arr: np.ndarray
    marsh_tfm: np.ndarray
    developed_arr: np.ndarray
    developed_tfm: np.ndarray
    open_area_arr: np.ndarray
    open_area_tfm: np.ndarray
    plot_save_path: str
    background_map_arr: np.ndarray
