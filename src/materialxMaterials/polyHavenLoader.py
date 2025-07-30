import requests
#import json
from pathlib import Path
import argparse
import zipfile

class PolyHavenLoader:
    def __init__(self):
        self.BASE_API = "https://api.polyhaven.com"
        self.ASSET_API = "https://api.polyhaven.com/assets"
        self.INFO_API = "https://api.polyhaven.com/info"
        self.FILES_API = "https://api.polyhaven.com/files"
        self.HEADERS = {
            "User-Agent": "MTLX_Polyaven_Loader/1.0",  # Required by PolyHaven API
        }

    def fetch_materialx_assets(self, resolution="1k"):
        parameters = {
            "type": "textures"
        }

        resp = requests.get(self.ASSET_API, headers=self.HEADERS, params=parameters)
        resp.raise_for_status()
        all_assets = resp.json()
        #print("fethced assets", all_assets.keys())

        materialx_assets = {}
        filtered_polyhaven_assets = {}

        for id, data in all_assets.items():
            if False:
                print(f"Checking asset id: '{id}'")
                resp = requests.get(f"{self.INFO_API}/{id}", headers=self.HEADERS)
                resp.raise_for_status()
                asset_data = resp.json()
                json_string = json.dumps(asset_data, indent=4)

            resp = requests.get(f"{self.FILES_API}/{id}", headers=self.HEADERS)
            resp.raise_for_status()
            files_data = resp.json()
            json_string = json.dumps(files_data, indent=4)

            mtlx_files = files_data.get("mtlx", [])
            if mtlx_files:
                # Look for 1K, 2K , 4K, and 8K versions
                one_k = mtlx_files.get(resolution)
                #two_k = mtlx_files.get("2k")
                #four_k = mtlx_files.get("4j")
                #eight_k = mtlx_files.get("8k")
                if one_k:
                    one_k_mtlx = one_k.get("mtlx")
                    texture_struct = {}
                    if one_k_mtlx:
                        #print(f"Found MaterialX files for '{one_k}'")
                        include_files = one_k_mtlx.get("include", {})
                        #print(f"Found include files for '{id}': {one_k}")
                        for path, data in include_files.items():
                            texture_url = data.get("url")
                            #print("Texture path:", path, "URL:", texture_url)
                            texture_struct[path] = texture_url
                    mtlx_url = one_k_mtlx.get("url")
                    if mtlx_url:
                        materialx_assets[id] = {
                            "url": mtlx_url,
                            "texture_files": texture_struct
                        }
                        json_string = json.dumps(materialx_assets[id], indent=4)
                        print(f"Found MaterialX for '{id}': {json_string}") 
                    # Create folder poly_have_data

                # Save asset data to JSON file
                #with open(f"polyhaven_data/{id}_data.json", "w") as f:
                #    json.dump(asset_data, f, indent=4)
                #    print(f"Saved asset data for '{id}' to polyhaven_data/{id}_data.json")

                filtered_polyhaven_assets[id] = data
        
            #if "materialx" in formats:
            #    materialx_assets[slug] = formats["materialx"]

        # Write all_assets to JSON file:
        Path("polyhaven_data").mkdir(parents=True, exist_ok=True)
        with open("polyhaven_assets.json", "w") as f:
            json.dump(all_assets, f, indent=4)
            print("Saved all assets to polyhaven_assets.json")

        return materialx_assets

    def download_asset(self, asset_list):
        # e.g. asset_list = {'polystyrene': {'url': 'https://.../polystyrene.mtlx', 'texture_files': {...}}}
        for id, asset in asset_list.items():
            url = asset.get("url")
            if not url:
                print(f"No MaterialX URL found for '{id}'")
                continue

            resp = requests.get(url, headers=self.HEADERS)
            resp.raise_for_status()
            mtlx_string = resp.text
            print(f"> Download MaterialX document {url}, length: {len(mtlx_string)} characters")

            texture_binaries = []
            for path, texture_url in asset.get("texture_files", {}).items():
                # Get texture files
                print(f"> Download texture from {texture_url} ...")
                texture_resp = requests.get(texture_url, headers=self.HEADERS)
                texture_resp.raise_for_status()            

                ext = Path(path).suffix.lower()
                name = Path(path).stem

                if ext == ".exr":
                    print(f"  > WARNING: EXR file present which may not be supported by MaterialX texture loader: {path}")
                texture_binaries.append((path, texture_resp.content))

            return id, mtlx_string, texture_binaries

    def save_materialx_with_textures(self, id, mtlx_string, texture_binaries, data_folder):
            # Create a zip file with MaterialX and textures
            filename = f"{id}_materialx.zip"
            filename = Path(data_folder) / filename
            with zipfile.ZipFile(filename, "w") as zipf:
                # Write MaterialX file
                zipf.writestr(f"{id}.mtlx", mtlx_string)
                # Write texture files
                for path, content in texture_binaries:
                    zipf.writestr(path, content)
            print(f"Saved zip: {filename}")

def main():
    parser = argparse.ArgumentParser(description="Fetch MaterialX assets from PolyHaven")
    parser.add_argument("-id", "--download_id", type=str, default="polystyrene", help="Filter ID to fetch MaterialX assets (e.g. 'polystyrene')")
    parser.add_argument("-res", "--download_resolution", type=str, default="1k", help="Resolution of the MaterialX assets to download (e.g. '1k', '2k', '4k', '8k') ")
    parser.add_argument("-f", "--fetch", type=str, default="polyhaven_materialx_assets.json", help="Fetch and save the MaterialX assets to a file")
    parser.add_argument("-l", "--load", type=str, default="polyhaven_materialx_assets.json", help="Load the MaterialX assets")
    parser.add_argument("-df", "--data_folder", type=str, default="data", help="Data folder to save / load MaterialX assets")

    args = parser.parse_args()
    fetch_location = args.fetch
    load_location = args.load
    data_folder = args.data_folder
    if not fetch_location and not load_location:
        print("Please specify --fetch or --load to perform an action.")
        return
    
    loader = PolyHavenLoader()

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