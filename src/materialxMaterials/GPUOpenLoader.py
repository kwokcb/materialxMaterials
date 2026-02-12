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
from io import BytesIO
from PIL import Image as PILImage
import base64

class GPUOpenMaterialLoader():
    '''
    This class is used to load materials from the GPUOpen material database.
    See: https://api.matlib.gpuopen.com/api/swagger/ for API information.
    '''
    def __init__(self):
        '''
        Initialize the GPUOpen material loader.
        '''
        ### Root URL for the GPUOpen material database
        self.root_url = 'https://api.matlib.gpuopen.com/api'
        ### URL for the materials
        self.url = self.root_url + '/materials'
        ### URL for the package information
        self.package_url = self.root_url + '/packages'
        ### URL for getting rendering information
        self.render_url = self.root_url + '/renders'
        ### List of title, preview url pairs for the materials
        self.materialPreviews = None
        ### List of materials
        self.materials = None
        ### List of material names
        self.materialNames = None
        ### List of render information
        self.renders = None

        ### Logger
        self.logger = logging.getLogger('GPUO')
        logging.basicConfig(level=logging.INFO)

    def writePackageDataToFile(self, data, outputFolder, title, url, unzipFile=True) -> bool:
        '''
        Write a package data to a file.
        @param data: The data to write.
        @param outputFolder: The output folder to write the file to.
        @param title: The title of the file.
        @param url: The URL for the material preview image.
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

            # Write a url.txt file with url information for the material preview
            urlFile = os.path.join(unzipFolder, 'url.txt')
            with open(urlFile, 'w') as f:
                f.write(url)

            self.logger.info(f'Unzipped to folder: "{unzipFolder}"')

        else:
            # Add the url.txt into the existing zip data
            zip_buffer = io.BytesIO()
            # Open the original zip data in append mode
            with zipfile.ZipFile(io.BytesIO(data), 'a', zipfile.ZIP_DEFLATED) as zip_in:
                # Copy all files to a new zip buffer
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                    for item in zip_in.infolist():
                        zip_out.writestr(item, zip_in.read(item.filename))
                    # Add url.txt
                    zip_out.writestr('url.txt', url)
            data = zip_buffer.getvalue()

            outputFile = os.path.join(outputFolder, f"{title}.zip")
            with open(outputFile, "wb") as f:
                self.logger.info(f'Write package to file: "{outputFile}"')
                f.write(data)


        return True
    
    def convertPilImageToBase64(self, image):
        """
        Convert a PIL image to a Base64 string.
        @param image: An instance of PIL.Image
        @return: Base64-encoded string of the image
        """
        pilImage = PILImage
        if not pilImage:            
            self.logger.debug('Pillow (PIL) image module not provided. Image data will not be converted to Base64.')
            return None
        if not image:
            self.logger.debug('No image data. Image data will not be converted to Base64.')
            return None

        # - Create an in-memory buffer
        # - Save the image to the buffer in PNG format
        # - Get the PNG file data from the buffer
        # - Encode the binary data to Base64
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        binary_data = buffer.getvalue()
        base64_encoded_data = base64.b64encode(binary_data).decode('utf-8')
        buffer.close()

        return base64_encoded_data    
    
    def extractPackageData(self, data, pilImage):
        '''
        Extract the package data from a zip file.
        @param data: The data to extract.
        @param pilImage: The PIL image module.
        @return: A list of extracted data of the form:
        [ { 'file_name': file_name, 'data': data, 'type': type } ]
        '''
        if not pilImage:
            pilImage = PILImage
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
            self.logger.info('No material loaded.')
            return [None, None]

        json_data = self.materials[listNumber]
        if not json_data:
            self.logger.info(f'No material for list {listNumber}.')
            return [None, None]

        jsonResults = None 
        jsonResult = None
        if "results" in json_data:
            jsonResults = json_data["results"]
            if len(jsonResults) <= materialNumber:
                self.logger.info(f'No material for index {materialNumber}.')
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
            self.logger.info(f'No packages for material {materialNumber}.')
            return [None, None]

        if len(jsonPackages) <= packageId:
            self.logger.info(f'No package for index {packageId}.')
            return [None, None]
        package_id = jsonPackages[packageId]

        if not package_id:
            self.logger.info(f'No package for index {packageId}.')
            return [None, None]

        url = f"{self.package_url}/{package_id}/download"
        data = requests.get(url).content

        title = jsonResult["title"]

        preview_url = self.getMaterialPreviewURL(title)
        return [data, title, preview_url]
    
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
                result = [data, title, url] = self.downloadPackage(listNumber, materialNumber, packageId)
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
        for materialList in self.materials:
            materialNumber = 0                
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
    
    def getMaterialPreviewURL(self, title) -> str:
        '''
        @breif Given the title of a material, return the URL for the material preview image.
        @param title: The title of the material to get the preview URL for.
        @return: The URL for the material preview image. Else empty string.
        '''
        url = ''
        if (self.materialPreviews == None):
            self.computeMaterialPreviews()
        if (not self.materialPreviews):
            return url
        
        for item in self.materialPreviews:
            if item['title'] == title:
                url = item['preview_url']
                break
        return url

    def getMaterialPreviews(self, force = False) -> list | None:
        if not self.materialPreviews or force:
            self.computeMaterialPreviews()
        return self.materialPreviews

    def computeMaterialPreviews(self) -> list:
        '''
        @brief Get the material preview URLs for the materials loaded from the GPUOpen material database.
        @return list of items of the form: { 'title': material_title, 'preview_url': url }
        If no materials or renders are loaded, then an empty list is returned.
        '''
        self.materialPreviews = []
        if (self.materials == None):
            return []
        if (self.renders == None):
            return []
        render_urls = self.renders["renders"]
        
        for materialList in self.materials:
            for material in materialList['results']:
                renders_order_list =  material['renders_order']
                material_title = material['title']

                if len(renders_order_list) > 0:
                    #print('renders_order_list:', renders_order_list)
                    render_lookup = renders_order_list[0]
                    # Look for item in "renders" list with "id" == render_lookup
                    for render in render_urls:
                        #print('render id:', render['id'], 'render_lookup:', render_lookup   )
                        if render['id'] == render_lookup:
                            url = render['thumbnail_url']
                            item = { 'title': material_title, 'preview_url': url }
                            self.materialPreviews.append(item)
                            #print(f'Found render for material: {item}')
                            break
                else:
                    self.logger.info(f'No renderings specified for material: {material_title}')
        return self.materialPreviews

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
    
    def getRenders(self, force=False) -> list:
        '''
        Get the rendering information returned from the GPUOpen material database.
        Will loop based on the linked-list of render info stored in the database.
        Currently the batch size requested is 100 render infos per batch.
        @param force: If true, forces a re-download of the render information. Default is false.
        @return: List of material lists
        '''
        if self.renders and not force:
            return self.renders

        self.renders = { "renders": [] }

        url = self.render_url
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

                # Extrac out the  "results": [] list
                results_list = jsonObject['results']
                for result in results_list:
                    self.renders["renders"].append(result)

                # Scan for next batch of materials
                nextQuery = jsonObject['next']
                if (nextQuery):
                    # Get limit and offset from this: 'https://api.matlib.gpuopen.com/api/renders/?limit=100&offset=100"'
                    # Split the string by '?'
                    queryParts = nextQuery.split('?')
                    # Split the string by '&'
                    queryParts = queryParts[1].split('&')
                    # Split the string by '='
                    limitParts = queryParts[0].split('=')
                    offsetParts = queryParts[1].split('=')
                    params['limit'] = int(limitParts[1])
                    params['offset'] = int(offsetParts[1])
                    self.logger.info(f'Fetch set of render infos: limit: {params["limit"]} offset: {params["offset"]}')
                else:
                    haveMoreMaterials = False
                    break
                
            else:
                self.logger.info(f'Error: {response.status_code}, {response.text}')

        return self.renders 

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

    def getMaterialFileNames(self, rootName) -> list:
        '''
        Get list of material file names based on root file name.
        @param rootName: The root name of the files to load. The files are assumed to be named: rootName_#.json
        '''
        filePaths = []
        rootName = os.path.basename(rootName)
        rootDir = os.path.dirname(rootName)
        if not rootDir:
            rootDir = '.'
        #print('RootDir:', rootDir)
        #print('RootName:', rootName)
        for root, dirs, files in os.walk(rootDir):
            for file in files:
                # Check that it ends with a number + ".json". e.g.
                # "GPUOpenMaterialX_0.json"
                if file.startswith(rootName) and file.endswith('.json') and file[len(rootName):-5].isdigit():
                    filePath = os.path.join(root, file)
                    filePaths.append(filePath)
        return filePaths

    def readPackageFiles(self) -> None:
        '''
        @brief Read the material files from the "data/GPUOpenMaterialX" folder in the install Python package.
        The files are expected to be named: 
        - "GPUOpenMaterialX_#.json" for material files,
        - "GPUOpenMaterialX_Previews_.json" for material preview information, and 
        - "GPUOpenMaterialX_Names.json" for material names.
        '''

        self.materials = []
        self.materialPreviews = []
        self.materialNames = []        

        # Read "data/GPUOpenMaterialX" files from install Python package
        # Get package:
        packageFolder = os.path.join(os.path.dirname(__file__), 'data/GPUOpenMaterialX')
        for fileName in os.listdir(packageFolder):
            filePath = os.path.join(packageFolder, fileName)
            self.logger.debug(f'> SCAN package file: "{filePath}"')
            # Check for files of this form: GPUOpenMaterialX_#.json
            if re.match(r'GPUOpenMaterialX_\d+\.json', fileName):
                self.logger.debug(f'> Read package file: "{filePath}"')
                with open(filePath) as f:
                    data = json.load(f)
                    results = data['results']
                    results_count = len(results)
                    self.materials.append(data)		
            elif fileName == 'GPUOpenMaterialX_Previews_.json':
                self.logger.debug(f'> Read package file: "{filePath}"')
                with open(filePath) as f:
                    data = json.load(f)
                    self.materialPreviews = data
            #elif fileName == 'GPUOpenMaterialX_Names.json':
            #    self.logger.debug(f'> Read package file: "{filePath}"')
            #    with open(filePath) as f:
            #        data = json.load(f)
            #        self.materialNames = data
            elif fileName == 'GPUOpenMaterialX_Renders_.json':
                self.logger.debug(f'> Read package file: "{filePath}"')
                with open(filePath) as f:
                    data = json.load(f)
                    self.renders = data

        # Better to extract the names from materials vs reading from file
        # which may be out of sync.
        self.getMaterialNames()

        self.logger.debug(f'Loaded {len(self.materials)} material files, '
                         f'{len(self.materialPreviews)} material previews, and '
                         f'{len(self.materialNames)} material names, '
                         f'{len(self.renders)} render files from package.')


    def readMaterialFiles(self, fileNames) -> list:
        '''
        Load the materials from a set of JSON files downloaded from
        the GPUOpen material database.
        '''
        self.materials = []
        for fileName in fileNames:
            with open(fileName) as f:
                data = json.load(f)
                results = data['results']
                results_count = len(results)
                self.materials.append(data)
        return self.materials

    def writeRenderFiles(self, folder, rootFileName) -> int:
        '''
        Write the render information to disk files.
        @param folder: The folder to write the files to.
        @param rootFileName: The root file name to use for the files.
        @return: The number of files written.
        '''
        if (self.renders == None):
            return 0

        os.makedirs(folder, exist_ok=True)
        # Write JSON to file
        fileName = rootFileName + '_.json'
        rendersFileName = os.path.join(folder, fileName)
        self.logger.info(f'> Write render info to file: "{rendersFileName}"')
        with open(rendersFileName, 'w') as f:
            json.dump(self.renders, f, indent=4)

    def writeMaterialPreviewFile(self, folder, rootFileName):
        '''
        Write the material preview information to disk files.
        @param folder: The folder to write the files to.
        @param rootFileName: The root file name to use for the files.
        '''
        if (self.materialPreviews == None):
            return 0

        os.makedirs(folder, exist_ok=True)
        # Write JSON to file
        fileName = rootFileName + '_.json'
        previewsFileName = os.path.join(folder, fileName)
        self.logger.info(f'> Write material preview info to file: "{previewsFileName}"')
        with open(previewsFileName, 'w') as f:
            json.dump(self.materialPreviews, f, indent=4)


    def writeMaterialFiles(self, folder, rootFileName) -> int:
        '''
        Write the materials to disk.
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
