
import logging as lg

from http import HTTPStatus
import requests # type: ignore
import os # type: ignore
#import inspect # type: ignore

import csv # type: ignore
import json # type: ignore

import MaterialX as mx # type: ignore
from typing import Optional

class AmbientCGLoader:
    '''
    @brief Class to load materials from the AmbientCG site.
    The class can convert the materials to MaterialX format for given target shading models.
    '''
    def __init__(self, mx_module, mx_stdlib : Optional[mx.Document] = None):
        '''
        @brief Constructor for the PhysicallyBasedMaterialLoader class. 
        Will initialize shader mappings and load the MaterialX standard library
        if it is not passed in as an argument.
        @param mx_module The MaterialX module. Required.
        @param mx_stdlib The MaterialX standard library. Optional.        
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

        ### URI for full asset information
        self.uri = 'https://ambientcg.com/api/v2/full_json'

        ### MaterialX module
        self.mx = mx_module
        ### MaterialX standard library
        self.stdlib = mx_stdlib
        ### Flag to indicate OpenPBR shader support
        self.support_openpbr = False

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
    
    def getMaterialNames(self, key='assetId') -> list:
        ''' 
        Get the list of material names.     
        @param key The key to use for the material name. Default is 'assetId' based
        on the version 2 ambientCG API.
        @return The list of material names
        '''
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

    def downloadMaterial(self, assetId, path='', imageFormat='PNG', imageResolution='1',
                         downloadAttributeKey = 'downloadAttribute', downloadLinkKey = 'downloadLink'):
        '''
        @brief Download a material with a given id and format + resolution for images.
        Default is to look for a 1K PNG variant.
        @param assetId The string id of the material
        @param path The output path for the download. Default is empty.
        @param imageFormat The image format to download. Default is PNG.
        @param imageResolution The image resolution to download. Default is 1.
        @param downloadAttributeKey The download attribute key. Default is 'downloadAttribute' based on the V2 ambientCG API.
        @param downloadLinkKey The download link key. Default is 'downloadLink' based on the V2 ambientCG API.
        @return None
        '''
        # Look item with the given assetId, imageFormat and imageResolution
        url = ''
        downloadAttribute = ''
        items = self.findMaterial(assetId)
        target = self.buildDownLoadAttribute(imageFormat, imageResolution)
        for item in items:
            downloadAttribute = item[downloadAttributeKey]
            if  downloadAttribute == target:
                url = item[downloadLinkKey]
                self.logger.info(f'Found Asset: {assetId}. Download Attribute: {downloadAttribute} -> {url}')

        if len(url) == 0:
            self.logger.error(f'No download link found for asset: {assetId}, attribute: {target}')
            return

        # Get local filename to save the file the content to
        filename = url.split("file=")[-1]
        filename = os.path.join(path, filename)

        try:
            # Send a GET request to the URL
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Write the file in chunks to avoid memory issues with large files
            # TBD: What is the "ideal" chunk size.
            CHUNK_SIZE = 8192
            with open(filename, "wb") as file:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    file.write(chunk)

            self.logger.info(f"File downloaded successfully and saved as: {filename}")
            
        except requests.exceptions.RequestException as e:
            self.logger.info(f"Error occurred while downloading the file: {e}")        

    def findMaterial(self, assetId, key='assetId'):
        '''
        @brief Get the list of materials matching a material identifier
        @param assetId Material string identifier
        @param key The key to lookup asset identifiers. Default is 'assetId' based on the version 2 ambientCG API.
        @return List of materials, or None if not found
        '''
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
        @brief Download the list of materials from the ambientCG site: "ttps://ambientCG.com/api/v2/downloads_csv"
        Takes the origina CSV file and remaps this into JSON for runtime.
        @return Materials list
        '''
        # URL of the CSV file
        url = "https://ambientCG.com/api/v2/downloads_csv"
        headers = {
            'Accept': 'application/csv'
        }
        parameters = {
            'method': 'PBRPhotogrammetry',
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

    def getMaterialsFromURL(self) -> dict:
        ''' 
        @brief Download the asset database and database materials 
        list from the ambientCG site.
        @return None
        '''
        self.database.clear()
        self.assets = None

        url = self.uri
        headers = {
            'Accept': 'application/json'
        }
        parameters = {
            'method': 'PBRPhotogrammetry',
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