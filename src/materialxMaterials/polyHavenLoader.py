'''
@file : polyHavenLoader.py
@brief: A module to fetch MaterialX assets from PolyHaven API and download them.
'''
import requests
import json
from pathlib import Path
import zipfile

class PolyHavenLoader:
    '''
    A class to fetch MaterialX assets from PolyHaven API and download them.    
    '''
    def __init__(self):
        '''
        Initialize the PolyHavenLoader with API endpoints and headers.
        '''
        self.BASE_API = "https://api.polyhaven.com"
        self.ASSET_API = "https://api.polyhaven.com/assets"
        self.INFO_API = "https://api.polyhaven.com/info"
        self.FILES_API = "https://api.polyhaven.com/files"
        self.HEADERS = {
            "User-Agent": "MTLX_Polyaven_Loader/1.0",  # Required by PolyHaven API
        }

    def fetch_materialx_assets(self, resolution="1k"):
        '''
        Fetch MaterialX assets from PolyHaven API and filter them by resolution.
        @param resolution: The resolution of the MaterialX assets to fetch (e.g. "1k", "2k", "4k", "8k").
        @return: A dictionary of MaterialX assets with their URLs and texture files.
        '''
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
        '''
        Download MaterialX asset and its textures from PolyHaven.
        e.g. asset_list = {'polystyrene': {'url': 'https://.../polystyrene.mtlx', 'texture_files': {...}}}
        
        @param asset_list: A dictionary of MaterialX assets with their URLs and texture files.
        @return: The ID of the downloaded asset, the MaterialX string, and a list of texture binaries.
        '''
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
        ''''
        Save MaterialX string and texture binaries to a zip file.'
        @param id: The ID of the MaterialX asset.
        @param mtlx_string: The MaterialX string content.
        @param texture_binaries: A list of tuples containing texture file paths and their binary content.
        @param data_folder: The folder to save the zip file.
        '''
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

