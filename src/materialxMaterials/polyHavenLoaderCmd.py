'''
@file: polyhavenLoaderCmd.py
@brief: A command-line interface to fetch MaterialX assets from PolyHaven and download them.
'''
from pathlib import Path
import argparse
import json
import polyHavenLoader

def main():
    parser = argparse.ArgumentParser(description="Fetch MaterialX assets from PolyHaven")
    parser.add_argument("-id", "--download_id", type=str, default="polystyrene", help="Filter ID to fetch MaterialX assets (e.g. 'polystyrene')")
    parser.add_argument("-res", "--download_resolution", type=str, default="1k", help="Resolution of the MaterialX assets to download (e.g. '1k', '2k', '4k', '8k') ")
    parser.add_argument("-f", "--fetch", type=str, default="polyhaven_materialx_assets.json", help="Fetch and save the MaterialX assets to a file")
    parser.add_argument("-l", "--load", type=str, default="polyhaven_materialx_assets.json", help="Load the MaterialX assets")
    parser.add_argument("-df", "--data_folder", type=str, default="data/PolyHavenMaterialX", help="Data folder to save / load MaterialX assets")

    args = parser.parse_args()
    fetch_location = args.fetch
    load_location = args.load
    data_folder = args.data_folder
    if not fetch_location and not load_location:
        print("Please specify --fetch or --load to perform an action.")
        return
    
    loader = polyHavenLoader.PolyHavenLoader()

    if load_location:
        load_location = Path(data_folder) / load_location
        with open(load_location, "r") as f:
            print(f"Loaded MaterialX assets from {load_location}")
            materialx_assets = json.load(f)
    elif fetch_location:
        fetch_location = Path(data_folder) / fetch_location
        print(f"Fetching MaterialX assets to {fetch_location}...")
        materialx_assets = loader.fetch_materialx_assets("polystyrene")
        with open(fetch_location, "w") as f:
            json.dump(materialx_assets, f, indent=4)
        print(f"FInished fetching MaterialX assets to {fetch_location}")

    download_id = args.download_id
    if download_id:
        # Find download entry by ID
            entry = materialx_assets.get(download_id)
            if entry:
                print(f"Downloading asset with ID '{download_id}'")
                asset_list = {download_id: entry}
                id, mtlx_string, texture_binaries = loader.download_asset(asset_list)                
                loader.save_materialx_with_textures(id, mtlx_string, texture_binaries, data_folder)

if __name__ == "__main__":
    main()