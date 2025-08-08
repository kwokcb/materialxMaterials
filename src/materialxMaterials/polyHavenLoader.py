'''
@file : polyHavenLoader.py
@brief: A module to fetch MaterialX assets from PolyHaven API and download them.
'''
import requests
import json
from pathlib import Path
import zipfile
import logging


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

        self.logger = logging.getLogger('PolyH')
        logging.basicConfig(level=self.logger.info)

    def fetch_materialx_assets(self, max_items=1, download_id=None):
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

        materialx_assets = {}
        filtered_polyhaven_assets = {}

        item_count = 0;
        for id, data in all_assets.items():

            if download_id and id != download_id:
                #self.logger.info(f"Skipping asset id: '{id}' (not matching {download_id})")
                continue

            # Get the thumbnail
            thumbnail_url = data.get("thumbnail_url")

            resp = requests.get(f"{self.FILES_API}/{id}", headers=self.HEADERS)
            resp.raise_for_status()
            files_data = resp.json()
            #json_string = json.dumps(files_data, indent=4)

            # Remove all keys other than "mtlx"
            files_data = {k: v for k, v in files_data.items() if k == "mtlx"}            

            mtlx_files = files_data.get("mtlx", [])
            if mtlx_files:

                self.logger.info(f"Found MaterialX data for '{id}'") 

                # Look for 1K, 2K , 4K, and 8K versions
                resolutions = {
                    "1k": None,
                    "2k": None,
                    "4k": None,
                    "8k": None
                }
                for resolution_key in resolutions.keys():
                    res = mtlx_files.get(resolution_key, None)
                    if not res:
                        continue

                    n_k_mtlx = res.get("mtlx")
                    texture_struct = {}
                    if n_k_mtlx:
                        #self.logger.info(f"Found MaterialX files for '{one_k}'")
                        include_files = n_k_mtlx.get("include", {})
                        #self.logger.info(f"Found include files for '{id}': {one_k}")
                        for path, data in include_files.items():
                            texture_url = data.get("url")
                            #self.logger.info("Texture path:", path, "URL:", texture_url)
                            texture_struct[path] = texture_url
                    mtlx_url = n_k_mtlx.get("url")
                    res_id = id + '___' + resolution_key
                    if mtlx_url:
                        materialx_assets[res_id] = {
                            "url": mtlx_url,
                            "texture_files": texture_struct,
                            "thumbnail_url": thumbnail_url
                        }
                        json_string = json.dumps(materialx_assets[res_id], indent=4)
                        #self.logger.info(f"Found MaterialX for '{res_id}': {json_string}") 
                        #self.logger.info(f"Found MaterialX for '{res_id}'") 
                    # Create folder poly_have_data

                    # Save asset data to JSON file
                    #with open(f"polyhaven_data/{id}_data.json", "w") as f:
                    #    json.dump(asset_data, f, indent=4)
                    #    self.logger.info(f"Saved asset data for '{id}' to polyhaven_data/{id}_data.json")

                filtered_polyhaven_assets[id] = files_data

            # Halt if download_id is specified and matches the current asset ID        
            if download_id == id:
                break

            # Halt if max_items is specified and reached
            if not download_id and max_items:
                item_count += 1
                if item_count >= max_items:
                    break            

            #if "materialx" in formats:
            #    materialx_assets[slug] = formats["materialx"]

        return materialx_assets, all_assets, filtered_polyhaven_assets

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
                self.logger.info(f"No MaterialX URL found for '{id}'")
                continue

            resp = requests.get(url, headers=self.HEADERS)
            resp.raise_for_status()
            mtlx_string = resp.text
            self.logger.info(f"Download MaterialX document {url}, length: {len(mtlx_string)} characters")

            texture_binaries = []
            for path, texture_url in asset.get("texture_files", {}).items():
                # Get texture files
                self.logger.info(f"Download texture from {texture_url} ...")
                texture_resp = requests.get(texture_url, headers=self.HEADERS)
                texture_resp.raise_for_status()            

                ext = Path(path).suffix.lower()
                name = Path(path).stem

                if ext == ".exr":
                    self.logger.info(f"  WARNING: EXR file present which may not be supported by MaterialX texture loader: {path}")
                texture_binaries.append((path, texture_resp.content))

            thumbnail_url = asset.get("thumbnail_url")
            if thumbnail_url:
                self.logger.info(f"Download thumbnail from {thumbnail_url} ...")                
                thumbnail_resp = requests.get(thumbnail_url, headers=self.HEADERS)
                thumbnail_resp.raise_for_status()
                
                clean_url = thumbnail_url
                # Strip any ? or # from the URL
                clean_url = clean_url.split('?')[0].split('#')[0]
                clean_url = clean_url.split('/')[-1]  # Get the last part of the URL
                extension = Path(clean_url).suffix.lower()
                texture_binaries.append((f"{id}_thumbnail.{extension}", thumbnail_resp.content))

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
        self.logger.info(f"Saved zip: {filename}")

