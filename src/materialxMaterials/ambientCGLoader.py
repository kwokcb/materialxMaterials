'''
@brief Utilities to extract materials from the ambientCG material database. 

See: https://docs.ambientcg.com/api/ for information on available API calls.
'''
import logging as lg

from http import HTTPStatus
import requests # type: ignore
import os # type: ignore
#import inspect # type: ignore

import csv # type: ignore
import json # type: ignore
import io # type: ignore
import zipfile # type: ignore

import MaterialX as mx # type: ignore
from typing import Optional

class AmbientCGLoader:
    '''
    @brief Class to load materials from the AmbientCG site.
    The class can convert the materials to MaterialX format for given target shading models.
    '''
    def __init__(self, mx_module, mx_stdlib : Optional[mx.Document] = None, api_version : str = 'v3'):
        '''
        @brief Constructor for the AmbientCGLoader class. 
        Will initialize shader mappings and load the MaterialX standard library
        if it is not passed in as an argument.
        @param mx_module The MaterialX module. Required.
        @param mx_stdlib The MaterialX standard library. Optional.
        @param api_version The ambientCG API version to use. Must be 'v2' or 'v3'. Default is 'v3'.
        '''
        
        ### logger is the logging object for the class
        self.logger = lg.getLogger('ACGLoader')
        lg.basicConfig(level=lg.INFO)

        ### Database of asset information
        self.database : dict = {}
        ### Reference to database found assets
        self.assets : dict = {}

        # Material download information
        ### List of materials in JSON format
        self.materials = None
        ### List of material names
        self.materialNames : list[str]= []
        ### List of materials in CSV format
        self.csv_materials = None

        # Downloaded material information
        ### Current downloaded material
        self.downloadMaterial = None
        ### Current downlaoded material file name
        self.downloadMaterialFileName = ''

        ### MaterialX module
        self.mx = mx_module
        ### MaterialX standard library
        self.stdlib = mx_stdlib
        ### Flag to indicate OpenPBR shader support
        self.support_openpbr = False
        ### AmbientCG API version to use ('v2' or 'v3'). V2 is deprecated upstream.
        self.api_version = api_version if api_version in ('v2', 'v3') else 'v3'

        if not mx_module:
            self.logger.critical(f'> {self._getMethodName()}: MaterialX module not specified.')
            return
        
        # Check for OpenPBR support which is only available in 1.39 and above
        version_major, version_minor, version_patch = self.mx.getVersionIntegers()
        self.logger.info(f'Using MaterialX version: {version_major}.{version_minor}.{version_patch}')
        if (version_major >=1 and version_minor >= 39) or version_major > 1:
            self.logger.debug('> OpenPBR shading model supported')
            self.support_openpbr = True

        # Load the MaterialX standard library if not provided
        if not self.stdlib:
            self.stdlib = self.mx.createDocument()
            libFiles = self.mx.loadLibraries(mx.getDefaultDataLibraryFolders(), mx.getDefaultDataSearchPath(), self.stdlib)            
            self.logger.debug(f'> Loaded standard library: {libFiles}')

    def setDebugging(self, debug : Optional[bool]=True):
        '''
        @brief Set the debugging level for the logger.
        @param debug True to set the logger to debug level, otherwise False.
        @return None
        '''
        if debug:
            self.logger.setLevel(lg.DEBUG)
        else:
            self.logger.setLevel(lg.INFO)

    def setApiVersion(self, api_version : str = 'v3'):
        '''
        @brief Set the ambientCG API version to use.
        @param api_version The API version to use. Must be 'v2' or 'v3'.
        '''
        if api_version not in ('v2', 'v3'):
            self.logger.warning(f'> {self._getMethodName()}: Invalid API version: {api_version}. Using v3.')
            api_version = 'v3'
        self.api_version = api_version
        self.logger.info(f'Using ambientCG API version: {api_version}')

    def getMaterialNames(self, key=None) -> list:
        ''' 
        Get the list of material names.     
        @param key The key to use for the material name. When None the default is used:
        'assetId' for the version 2 API, 'id' for the version 3 API.
        @return The list of material names
        '''
        if key is None:
            key = 'id' if self.api_version == 'v3' else 'assetId'
        self.materialNames.clear()
        unique_names = set()
        if self.materials:
            for item in self.materials:
                unique_names.add(item.get(key) )
        self.materialNames = list(sorted(unique_names))
        return self.materialNames

    def writeMaterialList(self, materialList, filename):
        '''
        @brief Write the material list in JSON format to a file
        @param materialList The list of materials to write
        @param filename The file path to write the list to
        @return None
        '''
        self.logger.info(f'Writing material list to file: {filename}')
        with open(filename, mode='w', encoding='utf-8') as json_file:
            json.dump(materialList, json_file, indent=4)

    def buildDownLoadAttribute(self, imageFormat='PNG', imageResolution='1'):
        '''
        @brief Build the download attribute string for a given image format and resolution
        Note: This is a hard-coded string format used by ambientCG. If this changes then this
        must be updated !
        @param imageFormat The image format to download
        @param imageResolution The image resolution to download
        @return The download attribute string
        '''
        target = f"{imageResolution}K-{imageFormat}"
        return target

    def getDownloadedMaterialInformation(self):
        '''
        @brief Get the current downloaded material information 
        '''
        return { 'filename': self.downloadMaterialFileName, 
                  'content': self.downloadMaterial }
    
    def clearDownloadMaterial(self):
        '''
        @brief Clear any cached current material asset
        '''
        if self.downloadMaterial:
            self.downloadMaterial.seek(0)  # Reset position
            self.downloadMaterial.truncate(0)  # Clear the buffer
            self.downloadMaterial = None
        self.downloadMaterialFileName = ''

    def writeDownloadedMaterialToFile(self, path=''):
        '''
        @brief Write the currently downloaded file to file
        @param path The output path for the material. Default is empty.
        '''
        haveDownload = len(self.downloadMaterialFileName) > 0 and self.downloadMaterial
        if not haveDownload:
            self.logger.warning('No current material downloaded')

        # Write the file in chunks to avoid memory issues with large files
        # TBD: What is the "ideal" chunk size.
        filename = self.downloadMaterialFileName
        filename = os.path.join(path, filename)

        # Write the file in chunks to avoid memory issues
        CHUNK_SIZE = 8192
        self.downloadMaterial.seek(0)
        with open(filename, "wb") as file:
            while True:
                chunk = self.downloadMaterial.read(CHUNK_SIZE)
                if not chunk:
                    break  # End of file
                file.write(chunk)        
        #with open(filename, "wb") as file:
        #    file.write(self.downloadMaterial.read())

        self.logger.info(f"Saved downloaded material to: {filename}")

    def downloadMaterialAsset(self, assetId, imageFormat='PNG', imageResolution='1',
                        downloadAttributeKey = 'downloadAttribute', downloadLinkKey = 'downloadLink'):
        '''
        @brief Download a material with a given id and format + resolution for images.
        Default is to look for a 1K PNG variant.
        @param assetId The string id of the material
        @param imageFormat The image format to download. Default is PNG.
        @param imageResolution The image resolution to download. Default is 1.
        @param downloadAttributeKey The download attribute key. Default is 'downloadAttribute' based on the V2 ambientCG API.
        @param downloadLinkKey The download link key. Default is 'downloadLink' based on the V2 ambientCG API.
        @return File name of downloaded content
        '''
        # Clear previous data
        self.clearDownloadMaterial()

        # Look item with the given assetId, imageFormat and imageResolution
        url = ''
        downloadAttribute = ''
        items = self.findMaterial(assetId)
        target = self.buildDownLoadAttribute(imageFormat, imageResolution)
        if self.api_version == 'v3':
            # In v3 the download variants are nested under the asset's "downloads" array
            for item in items:
                for download in item.get('downloads', []):
                    downloadAttribute = download.get('attributes')
                    if  downloadAttribute == target:
                        url = download.get('url')
                        self.logger.info(f'Found Asset: {assetId}. Download Attribute: {downloadAttribute} -> {url}')
        else:
            for item in items:
                downloadAttribute = item[downloadAttributeKey]
                if  downloadAttribute == target:
                    url = item[downloadLinkKey]
                    self.logger.info(f'Found Asset: {assetId}. Download Attribute: {downloadAttribute} -> {url}')

        if len(url) == 0:
            self.logger.error(f'No download link found for asset: {assetId}, attribute: {target}')
            return ''

        # Extract filename for save
        self.downloadMaterialFileName = url.split("file=")[-1]

        try:
            # Send a GET request to the URL
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Create an in-memory binary stream
            self.downloadMaterial = io.BytesIO()

            # Write the file in chunks to avoid memory issues with large files
            CHUNK_SIZE = 8192
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                self.downloadMaterial.write(chunk)            

            self.logger.info(f"Material file downloaded: {self.downloadMaterialFileName}")
            
        except requests.exceptions.RequestException as e:
            self.downloadMaterialFileName = ''

            self.logger.info(f"Error occurred while downloading the file: {e}") 

        return self.downloadMaterialFileName       

    def findMaterial(self, assetId, key=None):
        '''
        @brief Get the list of materials matching a material identifier
        @param assetId Material string identifier
        @param key The key to lookup asset identifiers. When None the default is used:
        'assetId' for the version 2 API, 'id' for the version 3 API.
        @return List of materials, or None if not found
        '''
        if key is None:
            key = 'id' if self.api_version == 'v3' else 'assetId'
        if self.materials:
            materialList = [item for item in self.materials if item.get(key) == assetId]
            return materialList
        return None

    def loadMaterialsList(self, fileName):
        '''
        @brief Load in the list of downloadable materials from file.
        @param fileName Name of JSON containing list
        @return Materials list
        '''
        with open(fileName, 'r') as json_file:
            self.materials = json.load(json_file)
        self.logger.info(f'Loaded materials list from: {fileName}')
        return self.materials

    def downloadMaterialsList(self):
        '''
        @brief Download the list of materials from the ambientCG site.
        For the version 2 API this uses the "downloads_csv" endpoint:
        "https://ambientCG.com/api/v2/downloads_csv". Takes the original CSV file
        and remaps this into JSON for runtime.
        For the version 3 API this uses the "assets" endpoint:
        "https://ambientCG.com/api/v3/assets".
        @return Materials list
        '''
        if self.api_version == 'v3':
            return self._downloadMaterialsListV3()

        # URL of the CSV file
        url = "https://ambientCG.com/api/v2/downloads_csv"
        headers = {
            'Accept': 'application/csv'
        }
        parameters = {
            'method': 'PBRPhotogrammetry', # TODO: Allow user filtering options
            'type': 'Material',
            'sort': 'Alphabet',
        }

        self.logger.info('Downloading materials CSV list...')
        response = requests.get(url, headers=headers, params=parameters)

        # Check if the request was successful
        if response.status_code == HTTPStatus.OK:
            # Decode the CSV content from the response
            self.csv_materials = response.content.decode("utf-8")
            
            # Parse the CSV content
            if self.csv_materials:
                csv_reader = csv.DictReader(self.csv_materials.splitlines())
            
                # Convert the CSV rows to a JSON object (list of dictionaries)
                self.materials = [row for row in csv_reader]

                self.logger.info("Downloaded CSV material list as JSON.")
            else:
                self.materials = None
                self.logger.warning("Failed to parse the CSV material content")
            
        else:
            self.materials = None
            self.logger.warning(f"Failed to fetch the CSV material content. HTTP status code: {response.status_code}")

        return self.materials

    def _fetchAssetsV3(self, limit=500, maxAssets=None):
        '''
        @brief Fetch the full list of assets using the version 3 "assets" endpoint,
        following pagination until all assets are retrieved (each page is capped at
        `limit` results, up to a maximum of 500).
        @param limit The number of assets to request per page. Maximum is 500.
        @param maxAssets Optional cap on the total number of assets to return.
        @return A tuple of (assets, status_code) where assets is the accumulated list
        of asset records and status_code is the HTTP status of the last request.
        '''
        url = "https://ambientCG.com/api/v3/assets"
        headers = {
            'Accept': 'application/json'
        }
        assets = []
        offset = 0
        pageLimit = min(limit, 500)
        totalResults = None

        while True:
            parameters = {
                'type': 'material',        # TODO: Allow user filtering options
                'sort': 'alphabet',
                'include': 'downloads,title,type',
                'limit': pageLimit,
                'offset': offset,
            }
            self.logger.info(f'Downloading materials list... offset={offset}, limit={pageLimit}')
            response = requests.get(url, headers=headers, params=parameters)
            if response.status_code != HTTPStatus.OK:
                self.logger.warning(f"Failed to fetch the materials list. HTTP status code: {response.status_code}")
                return assets, response.status_code

            data = response.json()
            pageAssets = data.get('assets', [])
            assets.extend(pageAssets)
            totalResults = data.get('totalResults')
            offset += len(pageAssets)

            if maxAssets is not None and len(assets) >= maxAssets:
                assets = assets[:maxAssets]
                break
            if len(pageAssets) == 0:
                break
            if totalResults is not None and offset >= totalResults:
                break

        return assets, HTTPStatus.OK

    def _downloadMaterialsListV3(self, maxAssets=None):
        '''
        @brief Download the list of materials using the version 3 "assets" endpoint.
        The response is a JSON object with an "assets" array. Each asset has an "id"
        and a "downloads" array of entries with keys: 'attributes', 'extension', 'url', 'size'.
        @param maxAssets Optional cap on the total number of assets to fetch.
        @return Materials list
        '''
        assets, status = self._fetchAssetsV3(maxAssets=maxAssets)
        if status == HTTPStatus.OK:
            self.materials = assets
            self.logger.info(f"Downloaded materials list: {len(self.materials)} assets")
        else:
            self.materials = None
        return self.materials

    def getDataBase(self):
        '''
        @brief Get asset database
        @return Asset database 
        '''
        return self.database
    
    def getDataBaseMaterialList(self):
        '''
        @brief Get asset database material list
        @return Material list
        '''
        return self.assets

    def downloadAssetDatabase(self) -> dict:
        ''' 
        @brief Download the asset database for materials from the ambientCG site.
        Uses the "full_json" endpoint for the version 2 API and the paginated "assets"
        endpoint for the version 3 API.
        @return None
        '''
        self.database.clear()
        self.assets = None

        if self.api_version == 'v3':
            assets, status = self._fetchAssetsV3()
            if status == HTTPStatus.OK:
                self.assets = assets
                self.database = {'totalResults': len(assets), 'assets': assets}
            else:
                self.logger.error(f'> Status: {status}')
        else:
            headers = {
                'Accept': 'application/json'
            }
            url = 'https://ambientcg.com/api/v2/full_json'
            parameters = {
                'method': 'PBRPhotogrammetry', # TODO: Allow user filtering options
                'type': 'Material',
                'sort': 'Alphabet',
            }
            response = requests.get(url, headers=headers, params=parameters)
            if response.status_code == HTTPStatus.OK:
                self.database = response.json()
                self.assets = self.database['foundAssets']
            else:
                self.logger.error(f'> Status: {response.status_code}, {response.text}')
            
    def writeDatabaseToFile(self, filename):
        '''
        @brief Write the database file
        @param filename The filename to write the JSON file to
        @return True if the file was written successfully, otherwise False
        '''
        if not self.database:
            self.logger.warning('No database to write')
            return False

        with open(filename, 'w') as json_file:
            json.dump(self.database, json_file, indent=4)
            return True
        
        return False

    @staticmethod
    def validateMaterialXDocument(self, doc):
        ''' 
        @brief Validate the MaterialX document 
        @param doc The MaterialX document to validate
        @return A tuple of (valid, errors) where valid is True if the document is valid, and errors is a list of errors if the document is invalid.
        '''
        if not self.mx:
            self.logger.critical(f'> {self._getMethodName()}: MaterialX module is required')        
            return False, '' 
        
        if not doc:
            self.logger.warning(f'> {self._getMethodName()}: MaterialX document is required')
            return False, ''

        valid, errors = doc.validate()
        return valid, errors

    @staticmethod
    def addComment(self, doc, commentString):
        '''
        @brief Add a comment to the MaterialX document
        @param doc The MaterialX document to add the comment to
        @param commentString The comment string to add
        @return None
        '''
        comment = doc.addChildOfCategory('comment')
        comment.setDocString(commentString)

    @staticmethod
    def getMaterialXString(self, doc):
        ''' 
        @brief Convert the MaterialX document to a string 
        @return The MaterialX document as a string
        '''
        if not self.mx:
            self.logger.critical(f'> {self._getMethodName()}: MaterialX module is required')
            return

        writeOptions = self.mx.XmlWriteOptions()
        writeOptions.writeXIncludeEnable = False
        writeOptions.elementPredicate = self.skipLibraryElement        
        mtlx = self.mx.writeToXmlString(doc, writeOptions)
        return mtlx