import rasterio
from rasterio.features import rasterize
import geopandas as gpd
from pathlib import Path


def vectorshape_to_raster(dtm_path, shape_gpkg, file_name="none", out_dir=r"C:\\MastersProgging\\Master_Project_main\\maps\\Area_masks"):
    """
    Funciton for converting vector shapes (.gpkg) to rasterdata (.tif)

    dtm_path:       For aligning raster with background map
    shape_gpkg:     Input vector shape file for convertion
    file_name:      Parameter for deciding output .tif file's name
    """
    # Load vector file and align CRS
    with rasterio.open(dtm_path) as src:
        dst_transform = src.transform
        dst_crs = src.crs
        out_shape = (src.height, src.width)
        profile = src.profile

    vector = gpd.read_file(shape_gpkg).to_crs(dst_crs)

    geom = [shapes for shapes in vector.geometry]

    # Rasterize: 1 = water , 0 = land
    raster = rasterize(
        geom,
        out_shape=out_shape,
        transform=dst_transform,
        fill=0,
        all_touched=True,
        default_value = 1,
        dtype="uint8",
    )

    # pick/save location
    out_dir = Path(out_dir) if out_dir else Path.cwd() / "data" / "processed" / "rasters"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{file_name}.tif"

    # Save aligned raster mask
    profile.update(driver="GTiff", dtype="uint8", nodata=0, count=1, compress="DEFLATE", predictor=2)
    with rasterio.open(out_path.as_posix(), "w", **profile) as dst:
        dst.write(raster, 1)

    print("Saved:", out_path.resolve())

    return None

### Main ###

# Run convertion of vector.gpkg to raster.tif using the DTM as template for alignment and resolution.
dtm_path = r"C:\MastersProgging\Master_Project_main\maps\DTMs\DTM.tif"
input_gpkg = r"C:\MastersProgging\Master_Project_main\maps\Area_masks\roads_buff_3m_mask_true.gpkg"
name = "roads_buff_3m_mask"

vectorshape_to_raster(dtm_path, input_gpkg, name)
