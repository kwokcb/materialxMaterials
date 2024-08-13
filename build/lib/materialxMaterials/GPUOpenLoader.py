import requests, json, os, io, re
import zipfile
from http import HTTPStatus
#import MaterialX as mx

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

    def writePackageDataToFile(self, data, outputFolder, title, unzipFile=True):
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

            print(f'Unzipped to folder: "{unzipFolder}"')

        else:            
            outputFile = os.path.join(outputFolder, f"{title}.zip")
            with open(outputFile, "wb") as f:
                print('Write package to file:', outputFile)
                f.write(data)

        return True

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

    def findMaterialsByName(self, materialName):
        '''
        Find materials by name.
        @param materialName: Regular expression to match the material name.
        @return: A list of materials that match the regular expression of the form:
        [ { 'listNumber': listNumber, 'materialNumber': materialNumber, 'title': title } ]
        '''
        if (self.materials == None):
            return None

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

    def updateMaterialNames(self):
        if (self.materials == None):
            return 0

        self.materialNames = []
        i = 0
        for materialList in self.materials:
            for material in materialList['results']:
                self.materialNames.append(material['title'])
                #print(f'Material [{i}] :', material['title'])
                i += 1
            #print(f'Number of materials: {i}')

        return len(self.materialNames)

    def getMaterials(self):

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
                #print('Number of JSON strings:', len(json_strings))
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
                    print('Fetch set of materials: limit:', params['limit'], 'offset:', params['offset'])
                else:
                    haveMoreMaterials = False
                    break
                
                dump = False
                if dump:
                    count = self.materials['count']
                    print('--------- Materials count:', count)
                    results = self.materials['results']
                    for result in results:
                        title = result['title']
                        mtlx_filename = result['mtlx_filename']
                        mtlx_material_name = result['mtlx_material_name']
                        print('title:', title, 'mtlx_filename:', mtlx_filename, 'mtlx_material_name:', mtlx_material_name)

            else:
                print(f'Error: {response.status_code}, {response.text}')

        return self.materials    

    def getMaterialsAsJsonString(self):
        '''
        Get the JSON strings for the materials
        '''
        results = []

        if (self.materials == None):
            return 0
        for material in self.materials:
            results.append(json.dumps(material, indent=4, sort_keys=True))
        return results

    def readMaterialFiles(self, fileNames):
        '''
        Load the materials from a set of JSON files downloaded from
        the GPUOpen material database.
        '''
        self.materials = []
        for fileName in fileNames:
            with open(fileName) as f:
                data = json.load(f)
                self.materials.append(data)

    def writeMaterialFiles(self, folder, rootFileName):
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
                print('> Write material to file:', materialFileName)
                with open(materialFileName, 'w') as f:
                    json.dump(material, f, indent=4, sort_keys=True)
                i += 1                    

        return i

