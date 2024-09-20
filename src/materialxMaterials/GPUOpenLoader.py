'''
@brief Utilities to extract materials from the GPUOpen material database. This is not a complete set of calls to extract out all material information but instead enough to find materials
and extract out specific packages from the list of available materials. 

See: https://api.matlib.gpuopen.com/api/swagger/ for information on available API calls.
'''

import requests, json, os, io, re, zipfile, logging # type: ignore
from http import HTTPStatus
# Note: MaterialX is not currently a dependency since no MaterialX processing is required.
#import MaterialX as mx

import io
import zipfile
from PIL import Image as pilImage

class GPUOpenMaterialLoader():
    '''
    This class is used to load materials from the GPUOpen material database.
    See: https://api.matlib.gpuopen.com/api/swagger/ for API information.
    '''
    def __init__(self):
        self.root_url = 'https://api.matlib.gpuopen.com/api'
        self.url = self.root_url + '/materials'
        self.package_url = self.root_url + '/packages'
        self.materials = None

        self.logger = logging.getLogger('GPUO')
        logging.basicConfig(level=logging.INFO)

    def writePackageDataToFile(self, data, outputFolder, title, unzipFile=True) -> bool:
        '''
        Write a package data to a file.
        @param data: The data to write.
        @param outputFolder: The output folder to write the file to.
        @param title: The title of the file.
        @param unzipFile: If true, the file is unzipped to a folder with the same name 
        as the title.
        @return: True if the package was written.
        '''
        if not data:
            return False

        if not os.path.exists(outputFolder):
            os.makedirs(outputFolder)
     
        if unzipFile:
            # Assuming `data` is the binary data of the zip file and `title` and `outputFolder` are defined
            unzipFolder = os.path.join(outputFolder, title)

            # Use BytesIO to handle the data in memory
            with io.BytesIO(data) as data_io:
                with zipfile.ZipFile(data_io, 'r') as zip_ref:
                    zip_ref.extractall(unzipFolder)

            self.logger.info(f'Unzipped to folder: "{unzipFolder}"')

        else:            
            outputFile = os.path.join(outputFolder, f"{title}.zip")
            with open(outputFile, "wb") as f:
                self.logger.info(f'Write package to file: "{outputFile}"')
                f.write(data)

        return True
    
    def extractPackageData(self, data, pilImage):
        '''
        Extract the package data from a zip file.
        @param data: The data to extract.
        @param pilImage: The PIL image module.
        @return: A list of extracted data of the form:
        [ { 'file_name': file_name, 'data': data, 'type': type } ]
        '''
        if not pilImage:
            self.logger.debug('Pillow (PIL) image module provided. Image data will not be extracted.')

        zip_object = io.BytesIO(data)

        extracted_data_list = []
        with zipfile.ZipFile(zip_object, 'r') as zip_file:
            # Iterate through the files in the zip archive
            for file_name in zip_file.namelist():
                # Extract each file into memory
                extracted_data = zip_file.read(file_name)
                if file_name.endswith('.mtlx'):
                    mtlx_string = extracted_data.decode('utf-8')
                    extracted_data_list.append( {'file_name': file_name, 'data': mtlx_string, 'type': 'mtlx'} )

                # If the data is a image, create a image in Python
                elif file_name.endswith('.png'):
                    if pilImage:
                        image = pilImage.open(io.BytesIO(extracted_data))        
                    else:
                        image = None
                    extracted_data_list.append( {'file_name': file_name, 'data': image, 'type': 'image'} )

        return extracted_data_list

    def downloadPackage(self, listNumber, materialNumber, packageId=0):
        '''
        Download a package for a given material from the GPUOpen material database.
        @param listNumber: The list number of the material to download.
        @param materialNumber: The material number to download.
        @param packageId: The package ID to download. 
            Packages are numbered starting at 0. Default is 0.
        with index 0 containing the smallest package (smallest resolution referenced textures).
        '''
        if self.materials == None or len(self.materials) == 0:
            return [None, None]

        json_data = self.materials[listNumber]
        if not json_data:
            return [None, None]

        jsonResults = None 
        jsonResult = None
        if "results" in json_data:
            jsonResults = json_data["results"]
            if len(jsonResults) <= materialNumber:
                return [None, None]
            else:
                jsonResult = jsonResults[materialNumber]
            
        if not jsonResult:
            return [None, None]
        
        # Get the package ID
        jsonPackages = None
        if "packages" in jsonResult:
            jsonPackages = jsonResult["packages"]
        if not jsonPackages:
            return [None, None]

        if len(jsonPackages) <= packageId:
            return [None, None]
        package_id = jsonPackages[packageId]

        if not package_id:
            return [None, None]

        url = f"{self.package_url}/{package_id}/download"
        data = requests.get(url).content

        title = jsonResult["title"]
        return [data, title]
    
    def downloadPackageByExpression(self, searchExpr, packageId=0):
        '''
        Download a package for a given material from the GPUOpen material database.
        @param searchExpr: The regular expression to match the material name.
        @param packageId: The package ID to download.
        @return: A list of downloaded packages of the form:
        '''
        downloadList = []

        foundList = self.findMaterialsByName(searchExpr)
        if len(foundList) > 0:
            for found in foundList:
                listNumber = found['listNumber']
                materialNumber = found['materialNumber']
                matName = found['title']
                self.logger.info(f'> Download material: {matName} List: {listNumber}. Index: {materialNumber}')
                result = [data, title] = self.downloadPackage(listNumber, materialNumber, packageId)
                downloadList.append(result)        
        return downloadList

    def findMaterialsByName(self, materialName) -> list:
        '''
        Find materials by name.
        @param materialName: Regular expression to match the material name.
        @return: A list of materials that match the regular expression of the form:
        [ { 'listNumber': listNumber, 'materialNumber': materialNumber, 'title': title } ]
        '''
        if (self.materials == None):
            return []

        materialsList = []
        listNumber = 0
        materialNumber = 0                
        for materialList in self.materials:
            for material in materialList['results']:
                if re.match(materialName, material['title'], re.IGNORECASE):
                    materialsList.append({ 'listNumber': listNumber, 'materialNumber': materialNumber, 'title': material['title'] })
                materialNumber += 1
            listNumber += 1

        return materialsList

    def getMaterialNames(self) -> list:
        '''
        Update the material names from the material lists.
        @return: List of material names. If no materials are loaded, then an empty list is returned.
        '''
        self.materialNames = []        
        if (self.materials == None):
            return []

        for materialList in self.materials:
            for material in materialList['results']:
                self.materialNames.append(material['title'])

        return self.materialNames

    def getMaterials(self) -> list:
        '''
        Get the materials returned from the GPUOpen material database.
        Will loop based on the linked-list of materials stored in the database.
        Currently the batch size requested is 100 materials per batch.
        @return: List of material lists
        '''

        self.materials = []
        self.materialNames = []

        url = self.url
        headers = {
            'accept': 'application/json'
        }

        # Get batches of materials. Start with the first 100.
        # Can apply more filters to this as needed in the future.
        # This will get every material in the database.        
        params = {
            'limit': 100,
            'offset': 0
        }
        haveMoreMaterials = True
        while (haveMoreMaterials):

            response = requests.get(url, headers=headers, params=params)

            if response.status_code == HTTPStatus.OK:
                
                raw_response = response.text
        
                # Split the response text assuming the JSON objects are concatenated
                json_strings = raw_response.split('}{')    
                #self.logger.info('Number of JSON strings:', len(json_strings))
                json_result_string = json_strings[0]
                jsonObject = json.loads(json_result_string)
                self.materials.append(jsonObject)

                # Scan for next batch of materials
                nextQuery = jsonObject['next']
                if (nextQuery):
                    # Get limit and offset from this: 'https://api.matlib.gpuopen.com/api/materials/?limit=100&offset=100"'
                    # Split the string by '?'
                    queryParts = nextQuery.split('?')
                    # Split the string by '&'
                    queryParts = queryParts[1].split('&')
                    # Split the string by '='
                    limitParts = queryParts[0].split('=')
                    offsetParts = queryParts[1].split('=')
                    params['limit'] = int(limitParts[1])
                    params['offset'] = int(offsetParts[1])
                    self.logger.info(f'Fetch set of materials: limit: {params["limit"]} offset: {params["offset"]}')
                else:
                    haveMoreMaterials = False
                    break
                
            else:
                self.logger.info(f'Error: {response.status_code}, {response.text}')

        return self.materials    

    def getMaterialsAsJsonString(self) -> list:
        '''
        Get the JSON strings for the materials
        @return: List of JSON strings for the materials. One string per material batch.
        '''
        results : list = []

        if (self.materials == None):
            return results
        for material in self.materials:
            results.append(json.dumps(material, indent=4, sort_keys=True))
        return results

    def readMaterialFiles(self, fileNames) -> list:
        '''
        Load the materials from a set of JSON files downloaded from
        the GPUOpen material database.
        '''
        self.materials = []
        for fileName in fileNames:
            with open(fileName) as f:
                data = json.load(f)
                self.materials.append(data)
        return self.materials

    def writeMaterialFiles(self, folder, rootFileName) -> int:
        '''
        Write the materials to a set of MaterialX files.
        @param folder: The folder to write the files to.
        @param rootFileName: The root file name to use for the files.
        @return: The number of files written.
        '''
        if (self.materials == None):
            return 0

        i = 0    
        if (len(self.materials) > 0):
            os.makedirs(folder, exist_ok=True)
            for material in self.materials:
                # Write JSON to file
                fileName = rootFileName + '_' + str(i) + '.json'
                materialFileName = os.path.join(folder, fileName)
                self.logger.info(f'> Write material to file: "{materialFileName}"')
                with open(materialFileName, 'w') as f:
                    json.dump(material, f, indent=4, sort_keys=True)
                i += 1                    

        return i

    def writeMaterialNamesToFile(self, fileName, sort=True):
        '''
        Write sorted list of the material names to a file in JSON format
        @param fileName: The file name to write the material names to.
        @param sort: If true, sort the material names.        
        '''
        if (self.materialNames == None):
            return

        with open(fileName, 'w') as f:
            json.dump(self.materialNames, f, indent=2, sort_keys=sort)
