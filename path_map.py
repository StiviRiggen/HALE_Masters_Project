from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
MAPS_DIR = PROJECT_ROOT / "maps"

def open_paths():
    
    # path to DTM:
    dtm_path = MAPS_DIR / "DTMs" / "DTM.tif"

    ### Mask paths ###
    # path to water mask:
    wm_path = MAPS_DIR / "Area_masks" / "water_mask.tif"

    # path to roads mask:
    roads_path = MAPS_DIR / "Area_masks" / "roads_buff_3m_mask.tif"

    # path to roads mask with buffer:
    buff_roads_path = MAPS_DIR / "Area_masks" / "roads_buff_20m_mask.tif"

    # path to forest mask:
    forest_path = MAPS_DIR / "Area_masks" / "forest_mask.tif"

    # path to marsh mask:
    marsh_path = MAPS_DIR / "Area_masks" / "marsh_mask.tif"

    # path to developed mask:
    developed_path = MAPS_DIR / "Area_masks" / "developed_mask.tif"

    # path to open area mask:
    open_area_path = MAPS_DIR / "Area_masks" / "open_area_mask.tif"
    
            
    # Path where autosaved plots shal be placed
    # TODO: Sette in if setning for lagring eller C:/Temp
    plot_save_path = PROJECT_ROOT / "output" / "Plot_"

    background_map_path = MAPS_DIR / "Background_maps" / "N100_Background.tif"

    return dtm_path, wm_path, roads_path, buff_roads_path, forest_path, marsh_path, developed_path, open_area_path, plot_save_path, background_map_path