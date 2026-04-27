'''
@brief Command to fetch MaterialX assets from PolyHaven and download them.
'''
from pathlib import Path
import argparse
import json
import logging
import polyHavenLoader

logger = logging.getLogger('POLYH_CMD')
logging.basicConfig(level=logging.INFO)

def PolyHavenLoaderCmd():
    '''
    @brief Command to fetch MaterialX assets from PolyHaven and download them.
    '''
    parser = argparse.ArgumentParser(description="Fetch MaterialX assets from PolyHaven")
    parser.add_argument("-id", "--download_id", type=str, default="", help="Filter ID to fetch MaterialX assets (e.g. 'polystyrene')")
    parser.add_argument("-dt", "--download_type", type=str, default="mtlx", help="Type of asset to download (e.g. 'mtlx', 'blend', 'gltf')")
    parser.add_argument("-res", "--download_resolution", type=str, default="1k", help="Resolution of the MaterialX assets to download (e.g. '1k', '2k', '4k', '8k') ")
    parser.add_argument("-fe", "--fetch", action='store_true', help="Fetch and save the MaterialX assets to a file")
    parser.add_argument("-l", "--load", action='store_true', help="Load the MaterialX assets")
    parser.add_argument("-df", "--data_folder", type=str, default="", help="Data folder to save / load MaterialX assets")
    parser.add_argument("-c", "--count", type=int, default=None, help="Number of assets to fetch (default: 1)")
    parser.add_argument('-exr', '--keep_exr', action='store_true', help="Keep EXR textures instead of converting to PNG (requires OpenImageIO)")
    parser.add_argument('-x', '--extract_zip', action='store_true', help="Extract downloaded ZIP files")

    args = parser.parse_args()
    download_type = args.download_type.lower()
    all_data_file = 'polyhaven_assets.json'
    filtered_data_file = 'filtered_polyhaven_assets.json'
    blend_data_file = "polyhaven_blender_assets.json"
    gltf_data_file = "polyhaven_gltf_assets.json"
    mtlx_data_file = "polyhaven_materialx_assets.json"
    fetch = args.fetch
    download_id = args.download_id
    resolution = args.download_resolution
    load = args.load or args.download_id != ""
    data_folder = args.data_folder
    
    loader = polyHavenLoader.PolyHavenLoader()

    materialx_assets = None
    blend_assets = None
    gltf_assets = None

    if fetch:
        fetch_count = args.count
        if fetch_count and fetch_count < 1:
            fetch_count = 1
        materialx_assets, all_assets, \
            filtered_polyhaven_assets, blender_assets, gltf_assets = \
            loader.fetch_materialx_assets(max_items=fetch_count, download_id=download_id, download_type=args.download_type)

        # Write all_assets to JSON file:        
        all_location = Path(data_folder) / all_data_file
        with open(all_location, "w") as f:
            json.dump(all_assets, f, indent=4)
            logger.info(f"Saved all assets to {all_location}")

        # Write filtered_polyhaven_assets to JSON file:
        filtered_location = Path(data_folder) / filtered_data_file
        with open(filtered_location, "w") as f:
            json.dump(filtered_polyhaven_assets, f, indent=4)
            logger.info(f"Saved MaterialX assets to {filtered_location}")

        # Write filtered MTLX, BLENDER, and GLTF assets to JSON files:
        mtlx_fetch_location = Path(data_folder) / mtlx_data_file
        with open(mtlx_fetch_location, "w") as f:
            logger.info(f"- Saving MaterialX assets to {mtlx_fetch_location}...")
            json.dump(materialx_assets, f, indent=4)

        blender_location = Path(data_folder) / blend_data_file
        with open(blender_location, "w") as f:
            json.dump(blender_assets, f, indent=4)
            logger.info(f"Saved Blender assets to {blender_location}")

        gltf_location = Path(data_folder) / gltf_data_file
        with open(gltf_location, "w") as f:
            json.dump(gltf_assets, f, indent=4)
            logger.info(f"Saved glTF assets to {gltf_location}")

    elif load:
        file_list = [mtlx_data_file, blend_data_file, gltf_data_file]
        for data_file in file_list:
            load_location = Path(data_folder) / data_file
            if not load_location.exists():
                load_location = Path(__file__).parent / "data" / "PolyHavenMaterialX" / data_file
                if not load_location.exists():
                    logger.info(f"Assets not found at {load_location}. Please run with --fetch to fetch assets first.")
                    return
            
            with open(load_location, "r") as f:
                logger.info(f"Loaded assets from {load_location}")
                if data_file == mtlx_data_file:
                    materialx_assets = json.load(f) 
                elif data_file == blend_data_file:
                    blend_assets = json.load(f)
                elif data_file == gltf_data_file:
                    gltf_assets = json.load(f)
            #json_string = json.dumps(materialx_assets, indent=4)
            #logger.info(f"MaterialX assets: {json_string}")

    keep_exr = args.keep_exr if args.keep_exr else False
    if args.download_type.lower() in ['blend']:
        keep_exr = True

    convert_exr_to_png = not keep_exr
    extract_zip = args.extract_zip if args.extract_zip else False
    
    if args.download_type.lower() == 'mtlx':
        # Download asset. For now only supporting MTLX download.
        if materialx_assets and download_id:
            # Find download entry by ID
            entry_id = download_id + '_' + resolution
            entry = materialx_assets.get(entry_id)
            if entry:
                logger.info(f"Downloading asset with ID '{download_id}', resolution '{resolution}'")
                asset_list = {entry_id: entry, resolution: resolution}
                id, mtlx_string, texture_binaries = loader.download_mtlx_asset(asset_list, convert_exr_to_png)    
                #logger.info(mtlx_string)            
                loader.save_materialx_with_textures(id, mtlx_string, texture_binaries, data_folder, extract_zip)
            else:
                logger.info(f"No asset found with ID '{entry_id}' in the MaterialX assets.")
        #else:
        #    logger.info("No operation specified.")

    elif args.download_type.lower() == 'blend':
        if blend_assets and download_id:
            # Find download entry by ID
            entry_id = download_id + '_' + resolution
            entry = blend_assets.get(entry_id)
            if entry:
                logger.info(f"Downloading Blender asset with ID '{download_id}', resolution '{resolution}'")
                asset_list = {entry_id: entry, resolution: resolution}
                id, blend_binary, texture_binaries = loader.download_blender_asset(asset_list)    
                loader.save_blender_with_textures(id, blend_binary, texture_binaries, data_folder, extract_zip)
            else:
                logger.info(f"No asset found with ID '{entry_id}' in the MaterialX assets.")
        #else:
        #    logger.info("No operation specified.")

    elif args.download_type.lower() == 'gltf':
        if gltf_assets and download_id:
            # Find download entry by ID
            entry_id = download_id + '_' + resolution
            entry = gltf_assets.get(entry_id)
            if entry:
                logger.info(f"Downloading glTF asset with ID '{download_id}', resolution '{resolution}'")
                asset_list = {entry_id: entry, resolution: resolution}
                id, gltf_ascii, texture_binaries = loader.download_gltf_asset(asset_list)    
                loader.save_gltf_with_textures(id, gltf_ascii, texture_binaries, data_folder, extract_zip)
            else:
                logger.info(f"No asset found with ID '{entry_id}' in the MaterialX assets.")
        #else:
        #    logger.info("No operation specified.")

if __name__ == "__main__":
    PolyHavenLoaderCmd()