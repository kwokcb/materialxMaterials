'''
@brief Module to fetch MaterialX assets from PolyHaven API and download them.
'''
import requests
import json
from pathlib import Path
import zipfile
import logging
import io
import tempfile
import os
import MaterialX as mx

HAVE_OPENIMAGEIO = False
try:
    import OpenImageIO as oiio
    import numpy as np
    HAVE_OPENIMAGEIO = True
except ImportError:
    print("OpenImageIO or numpy not installed. EXR image conversion not supported.")    

class PolyHavenLoader:
    """
    @brief Fetch MaterialX assets from PolyHaven API and download them.

    This class provides methods to fetch and download MaterialX assets and textures from PolyHaven.
    """
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

        # Keys for supported asset types
        self.MTLX_KEY = 'mtlx'
        self.GLTF_KEY = 'gltf'
        self.BLEND_KEY = 'blend'

        self.logger = logging.getLogger('PolyH')
        logging.basicConfig(level=self.logger.info)

    def fetch_materialx_assets(self, max_items=1, download_id=None, download_type=None):
        '''
        Fetch MaterialX assets from PolyHaven API and filter them by resolution.

        @param max_items Maximum number of assets to fetch. If None, fetch all.
        @param download_id If set, only fetch asset with this ID.
        @param download_type Type of asset to download (e.g. 'mtlx', 'blend', 'gltf'). Default is None which means to fetch MaterialX
        @return Tuple (materialx_assets, all_assets, filtered_polyhaven_assets):
            - materialx_assets: Dictionary of MaterialX assets with URLs and texture files.
            - all_assets: All assets returned by PolyHaven API.
            - filtered_polyhaven_assets: Filtered assets containing only MaterialX files.
        '''
        parameters = {
            "type": "textures"
        }

        resp = requests.get(self.ASSET_API, headers=self.HEADERS, params=parameters)
        resp.raise_for_status()
        all_assets = resp.json()

        materialx_assets = {}
        gltf_assets = {}
        blender_assets = {}
        filtered_polyhaven_assets = {}

        # Look for 1K, 2K , 4K, and 8K versions
        resolutions = {
            "1k": None,
            "2k": None,
            "4k": None,
            "8k": None
        }

        # Default to fetching MaterialX assets if no download type specified
        if not download_type:
            download_type = self.MTLX_KEY

        item_count = 0
        for id, data in all_assets.items():

            found_gltf = False
            found_blend = False
            found_mtlx = False

            if download_id and id != download_id:
                #self.logger.info(f"Skipping asset id: '{id}' (not matching {download_id})")
                continue

            # Get the thumbnail
            thumbnail_url = data.get("thumbnail_url")

            resp = requests.get(f"{self.FILES_API}/{id}", headers=self.HEADERS)
            resp.raise_for_status()
            files_data = resp.json()
            #json_string = json.dumps(files_data, indent=4)
            #print(f"Files data for asset '{id}': {json_string}")

            blend_files = files_data.get(self.BLEND_KEY, [])
            if blend_files:
                found_blend = True

                for resolution_key in resolutions.keys():
                    res = blend_files.get(resolution_key, None)
                    if not res:
                        continue

                    n_k_mtlx = res.get(self.BLEND_KEY)
                    texture_struct = {}
                    if n_k_mtlx:
                        include_files = n_k_mtlx.get("include", {})
                        for path, data in include_files.items():
                            texture_url = data.get("url")
                            texture_struct[path] = texture_url
                    url = n_k_mtlx.get("url")
                    res_id = id + '_' + resolution_key
                    if url:
                        blender_assets[res_id] = {
                            "url": url,
                            "texture_files": texture_struct,
                            "thumbnail_url": thumbnail_url
                        }                

                if download_id == id and download_type == self.BLEND_KEY:
                    break

            gltf_files = files_data.get(self.GLTF_KEY, [])
            if gltf_files:
                found_gltf = True

                for resolution_key in resolutions.keys():
                    res = gltf_files.get(resolution_key, None)
                    if not res:
                        continue

                    n_k_mtlx = res.get(self.GLTF_KEY)
                    texture_struct = {}
                    if n_k_mtlx:
                        include_files = n_k_mtlx.get("include", {})
                        for path, data in include_files.items():
                            texture_url = data.get("url")
                            texture_struct[path] = texture_url
                    url = n_k_mtlx.get("url")
                    res_id = id + '_' + resolution_key
                    if url:
                        gltf_assets[res_id] = {
                            "url": url,
                            "texture_files": texture_struct,
                            "thumbnail_url": thumbnail_url
                        }      

                # Halt if download_id is specified and matches the current asset ID and download type
                if download_id == id and download_type == self.GLTF_KEY:
                    break


            # Remove all keys other than "mtlx"
            #files_data = {k: v for k, v in files_data.items() if k == "mtlx"}            
            mtlx_files = files_data.get(self.MTLX_KEY, [])
            if mtlx_files:
                found_mtlx = True

                for resolution_key in resolutions.keys():
                    res = mtlx_files.get(resolution_key, None)
                    if not res:
                        continue

                    n_k_mtlx = res.get(self.MTLX_KEY)
                    texture_struct = {}
                    if n_k_mtlx:
                        include_files = n_k_mtlx.get("include", {})
                        for path, data in include_files.items():
                            texture_url = data.get("url")
                            texture_struct[path] = texture_url
                    mtlx_url = n_k_mtlx.get("url")
                    res_id = id + '_' + resolution_key
                    if mtlx_url:
                        materialx_assets[res_id] = {
                            "url": mtlx_url,
                            "texture_files": texture_struct,
                            "thumbnail_url": thumbnail_url
                        }

            filtered_polyhaven_assets[id] = files_data

            self.logger.info(f"Id: '{id}' has blender: {found_blend}, glTF: {found_gltf}, mtlx: {found_mtlx}")

            # Halt if download_id is specified and matches the current asset ID and download type
            if download_id == id and download_type == self.MTLX_KEY:
                break

            # Halt if max_items is specified and reached
            if not download_id and max_items:
                item_count += 1
                if item_count >= max_items:
                    break            

            #if "materialx" in formats:
            #    materialx_assets[slug] = formats["materialx"]

        return materialx_assets, all_assets, filtered_polyhaven_assets, blender_assets, gltf_assets

    def download_gltf_asset(self, asset_list):
        '''
        Download glTF asset from PolyHaven.

        @param asset_list Dictionary of glTF assets with URLs and texture files.
        @return Tuple (id, gltf_ascii, texture_binaries):
            - id: ID of the downloaded asset.
            - gltf_ascii: The glTF file as ASCII string.
            - texture_binaries: List of tuples (path, binary content) for textures and thumbnails
        '''
        for id, asset in asset_list.items():
            url = asset.get("url")
            if not url:
                self.logger.info(f"No glTF URL found for '{id}'")
                continue
            if not url.endswith(".gltf") and not url.endswith(".glb"):
                self.logger.info(f"Invalid glTF URL for '{id}': {url}")
                continue

            resp = requests.get(url, headers=self.HEADERS)
            resp.raise_for_status()
            if url.endswith(".glb"):
                self.logger.info(f"Downloaded glTF binary file {url}, size: {len(resp.content)} bytes")
                gltf_content = resp.content
            elif url.endswith(".gltf"):
                gltf_content = resp.text
                self.logger.info(f"Download glTF file {url}, length: {len(gltf_content)} characters")   

            texture_binaries = []
            for path, texture_url in asset.get("texture_files", {}).items():
                self.logger.info(f"Download texture from {texture_url} ...")
                texture_resp = requests.get(texture_url, headers=self.HEADERS)
                texture_resp.raise_for_status()            
                texture_content = texture_resp.content
                texture_binaries.append((path, texture_content))

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
                texture_binaries.append((f"{id}_thumbnail{extension}", thumbnail_resp.content))
            return id, gltf_content, texture_binaries

    def download_blender_asset(self, asset_list):
        '''
        Download Blender asset from PolyHaven.

        @param asset_list Dictionary of Blender assets with URLs and texture files.
        @return Tuple (id, blend_binary, texture_binaries):
            - id: ID of the downloaded asset.
            - blend_binary: The Blender file as binary content.
            - texture_binaries: List of tuples (path, binary content) for textures and thumbnails.
        '''
        for id, asset in asset_list.items():
            url = asset.get("url")
            if not url:
                self.logger.info(f"No Blender URL found for '{id}'")
                continue

            resp = requests.get(url, headers=self.HEADERS)
            resp.raise_for_status()
            blend_binary = resp.content
            self.logger.info(f"Download Blender file {url}, size: {len(blend_binary)} bytes")   

            texture_binaries = []
            for path, texture_url in asset.get("texture_files", {}).items():
                self.logger.info(f"Download texture from {texture_url} ...")
                texture_resp = requests.get(texture_url, headers=self.HEADERS)
                texture_resp.raise_for_status()            
                texture_content = texture_resp.content
                texture_binaries.append((path, texture_content))

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
                texture_binaries.append((f"{id}_thumbnail{extension}", thumbnail_resp.content))
            return id, blend_binary, texture_binaries                

    def download_mtlx_asset(self, asset_list, convert_exr_to_png=True):
        '''
        Download MaterialX asset and its textures from PolyHaven.

        @param asset_list Dictionary of MaterialX assets with URLs and texture files.
        @param convert_exr_to_png If True, attempt to use PNG images instead of EXR if available other attempt 
        to convert using OpenImageIO if installed. Default is to use PNG if possible, and convert EXR to PNG if OpenImageIO is available.
        @return Tuple (id, mtlx_string, texture_binaries):
            - id: ID of the downloaded asset.
            - mtlx_string: The MaterialX document as a string.
            - texture_binaries: List of tuples (path, binary content) for textures and thumbnails.
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
            download_texture_names = []
            for path, texture_url in asset.get("texture_files", {}).items():
                # Get texture files
                ext = Path(path).suffix.lower()
                texture_content = None

                if ext == ".exr" and convert_exr_to_png:
                    # Replace /exr and .exr with /png and .png in the URL to check if a PNG version is available  
                    old_texture_url = texture_url  
                    texture_url = texture_url.replace("/exr/", "/png/").replace(".exr", ".png")
                    texture_resp = requests.get(texture_url, headers=self.HEADERS)
                    texture_resp.raise_for_status()            
                    texture_content = texture_resp.content
                    if texture_content:
                        self.logger.info(f"Download {texture_url} instead of {old_texture_url} SUCCESSFUL")
                        ext = ".png"
                        # Update extension in the path to .png
                        old_path = path
                        path = str(Path(path).with_suffix(ext))
                        self.logger.info(f"- Updating texture path from {old_path} to {path}")

                    else:
                        self.logger.info(f"Download {texture_url} instead of {old_texture_url} FAILED")

                if not texture_content:
                    self.logger.info(f"Download texture from {texture_url} ...")
                    texture_resp = requests.get(texture_url, headers=self.HEADERS)
                    texture_resp.raise_for_status()            
                    texture_content = texture_resp.content

                name = Path(path).stem

                if ext == ".exr":
                    if HAVE_OPENIMAGEIO and convert_exr_to_png:
                        self.logger.info(f"Converting EXR to PNG for texture: {path}")
                        # Write EXR bytes to a temporary file
                        with tempfile.NamedTemporaryFile(suffix=".exr", delete=False) as tmp_exr:
                            tmp_exr.write(texture_content)
                            tmp_exr_path = tmp_exr.name
                        try:
                            inbuf = oiio.ImageInput.open(tmp_exr_path)
                            if inbuf:
                                spec = inbuf.spec()
                                pixels = inbuf.read_image(format=oiio.UINT8)
                                inbuf.close()
                                # Write PNG to another temporary file
                                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_png:
                                    outbuf = oiio.ImageOutput.create(tmp_png.name)
                                    if outbuf:
                                        outbuf.open(tmp_png.name, spec)
                                        outbuf.write_image(pixels)
                                        outbuf.close()
                                        tmp_png.seek(0)
                                        png_bytes = tmp_png.read()
                                        png_name = f"{name}.png"
                                        texture_binaries.append((png_name, png_bytes))

                                        continue  # Skip adding the original EXR
                            else:
                                self.logger.info("Failed to read EXR with OpenImageIO")
                        finally:
                            os.remove(tmp_exr_path)
                            if 'tmp_png' in locals():
                                os.remove(tmp_png.name)
                    self.logger.info(f"  WARNING: EXR file present which may not be supported by MaterialX texture loader: {path}")

                # Get file name from path
                download_texture_name = path.split('/')[-1]
                download_texture_names.append(download_texture_name)

                texture_binaries.append((path, texture_content))

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
                texture_binaries.append((f"{id}_thumbnail{extension}", thumbnail_resp.content))

            # Replace .exr with .png in mtlx_string
            for name in download_texture_names:
                extension = Path(name).suffix.lower()                
                exr_name = name.replace(extension, ".exr")
                # Replace exr_name with name in the mtlx_string
                mtlx_string = mtlx_string.replace(exr_name, name)

            before_mtlx_string = mtlx_string
            mtlx_string = mtlx_string.replace(".exr", ".png")
            if (before_mtlx_string != mtlx_string):
                self.logger.info(f"Updated MaterialX string to reference PNG texture instead of EXR for {path}")
                #self.logger.info(mtlx_string)

            return id, mtlx_string, texture_binaries

    def save_blender_with_textures(self, id, blend_binary, texture_binaries, data_folder, extract_zip=False):
        '''
        Save Blender file and texture binaries to a zip file.

        @param id The ID of the Blender asset.
        @param blend_binary The Blender file as binary content.
        @param texture_binaries List of tuples (path, binary content) for textures and thumbnails.
        @param data_folder Folder to save the zip file.
        @param extract_zip If True, extract the zip file after saving zip.
        @return None
        '''
        # Create a zip file with Blender file and textures
        filename = f"{id}_blender.zip"
        filename = Path(data_folder) / filename
        with zipfile.ZipFile(filename, "w") as zipf:
            # Write Blender file
            zipf.writestr(f"{id}.blend", blend_binary)
            # Write texture files
            for path, content in texture_binaries:
                zipf.writestr(path, content)
        self.logger.info(f"Saved zip: {filename}")

        # Save zip contents to folder
        extract_folder = Path(data_folder) / f"{id}_blender"
        if extract_zip:
            with zipfile.ZipFile(filename, "r") as zipf:
                zipf.extractall(extract_folder)
            self.logger.info(f"Extracted zip contents to folder: {extract_folder}")

    def save_gltf_with_textures(self, id, gltf_ascii, texture_binaries, data_folder, extract_zip=False):
        '''
        Save glTF file and texture binaries to a zip file.

        @param id The ID of the glTF asset.
        @param gltf_ascii The glTF file as ASCII string.
        @param texture_binaries List of tuples (path, binary content) for textures and thumbnails.
        @param data_folder Folder to save the zip file.
        @param extract_zip If True, extract the zip file after saving zip.
        @return None
        '''
        # Create a zip file with glTF file and textures
        filename = f"{id}_gltf.zip"
        filename = Path(data_folder) / filename
        with zipfile.ZipFile(filename, "w") as zipf:
            # Write glTF file
            zipf.writestr(f"{id}.gltf", gltf_ascii)
            # Write texture files
            for path, content in texture_binaries:
                zipf.writestr(path, content)
        self.logger.info(f"Saved zip: {filename}")

        # Save zip contents to folder
        extract_folder = Path(data_folder) / f"{id}_gltf"
        if extract_zip:
            with zipfile.ZipFile(filename, "r") as zipf:
                zipf.extractall(extract_folder)
            self.logger.info(f"Extracted zip contents to folder: {extract_folder}")

    def save_materialx_with_textures(self, id, mtlx_string, texture_binaries, data_folder, extract_zip=False):
        '''
        Save MaterialX string and texture binaries to a zip file.

        @param id The ID of the MaterialX asset.
        @param mtlx_string The MaterialX string content.
        @param texture_binaries List of tuples (path, binary content) for textures and thumbnails.
        @param data_folder Folder to save the zip file.
        @param extract_zip If True, extract the zip file after saving zip.
        @return None
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

        # Save zip contents to folder
        extract_folder = Path(data_folder) / f"{id}_materialx"
        if extract_zip:
            with zipfile.ZipFile(filename, "r") as zipf:
                zipf.extractall(extract_folder)
            self.logger.info(f"Extracted zip contents to folder: {extract_folder}")

