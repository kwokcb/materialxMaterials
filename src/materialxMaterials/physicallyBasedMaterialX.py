'''
@brief Class to load Physically Based Materials from the PhysicallyBased site.
and convert the materials to MaterialX format for given target shading models.
'''

import requests, json, os, inspect
import logging as lg 
from http import HTTPStatus
import MaterialX as mx

class PhysicallyBasedMaterialLoader:
    '''
    @brief Class to load Physically Based Materials from the PhysicallyBased site.
    The class can convert the materials to MaterialX format for given target shading models.
    '''
    def __init__(self, mx_module, mx_stdlib : mx.Document = None):
        '''
        @brief Constructor for the PhysicallyBasedMaterialLoader class. 
        Will initialize shader mappings and load the MaterialX standard library
        if it is not passed in as an argument.
        @param mx_module The MaterialX module. Required.
        @param mx_stdlib The MaterialX standard library. Optional.        
        '''
        self.logger = lg.getLogger('PBMXLoader')
        lg.basicConfig(level=lg.INFO)

        self.materials = {}
        self.materialNames = []
        self.uri = 'https://api.physicallybased.info/materials'
        self.doc = None
        self.mx = mx_module
        self.stdlib = mx_stdlib
        self.MTLX_NODE_NAME_ATTRIBUTE = 'nodename'
        self.support_openpbr = False

        if not mx_module:
            self.logger.critical(f'> {self._getMethodName()}: MaterialX module not specified.')
            return
        
        # Check for OpenPBR support which is only available in 1.39 and above
        version_major, version_minor, version_patch = self.mx.getVersionIntegers()
        self.logger.debug(f'> MaterialX version: {version_major}.{version_minor}.{version_patch}')
        if (version_major >=1 and version_minor >= 39) or version_major > 1:
            self.logger.debug('> OpenPBR shading model supported')
            self.support_openpbr = True

        self.initializeInputRemapping()

        # Load the MaterialX standard library if not provided
        if not self.stdlib:
            self.stdlib = self.mx.createDocument()
            libFiles = self.mx.loadLibraries(mx.getDefaultDataLibraryFolders(), mx.getDefaultDataSearchPath(), self.stdlib)            
            self.logger.debug(f'> Loaded standard library: {libFiles}')

    def setDebugging(self, debug=True):
        '''
        @brief Set the debugging level for the logger.
        @param debug True to set the logger to debug level, otherwise False.
        @return None
        '''
        if debug:
            self.logger.setLevel(lg.DEBUG)
        else:
            self.logger.setLevel(lg.INFO)

    def getInputRemapping(self, shadingModel) -> dict:
        '''
        @brief Get the remapping keys for a given shading model.
        @param shadingModel The shading model to get the remapping keys for.
        @return A dictionary of remapping keys.
        '''
        if (shadingModel in self.remapMap):
            return self.remapMap[shadingModel]

        self.logger.warn(f'> No remapping keys found for shading model: {shadingModel}')
        return {}

    def initializeInputRemapping(self): 
        ''' 
        @brief Initialize remapping keys for different shading models.
        The currently supported shading models are:
        - standard_surface
        - open_pbr_surface
        - gltf_pbr
        @return None
        '''
        # Remap keys for Autodesk Standard Surface shading model. 
        standard_surface_remapKeys = {
            'color': 'base_color',
            'specularColor': 'specular_color',
            'roughness': 'specular_roughness',
            #'metalness': 'metalness',
            'ior': 'specular_IOR',
            #'transmission': 'transmission',
            'transmission_color': 'transmission_color',
            'thinFilmIor' : 'thin_film_IOR',
            'thinFilmThickness' : 'thin_film_thickness',
            'transmissionDispersion' : 'transmission_dispersion',
        }
        # Remap keys for OpenPBR shading model.
        openpbr_remapKeys = {
            'color': 'base_color',
            'specularColor': 'specular_color',
            'roughness': 'specular_roughness', # 'base_diffuse_roughness',
            'metalness': 'base_metalness',
            'ior': 'specular_ior',
            'transmission': 'transmission_weight',
            'transmission_color': 'transmission_color',
            'subsurfaceRadius': 'subsurface_radius',
            'thinFilmIor' : 'thinfilm_ior',
            'thinFilmThickness' : 'thinfilm_thickness',
            'transmissionDispersion' : 'transmission_dispersion_scale',
        }
        # Remap keys for Khronos glTF shading model.
        gltf_remapKeys = {
            'color': 'base_color',
            'specularColor': 'specular_color',
            'roughness': 'roughness',
            'metalness': 'metallic',
            #'ior': 'ior',
            #'transmission': 'transmission',
        }

        self.remapMap = {}
        self.remapMap['standard_surface'] = standard_surface_remapKeys; 
        self.remapMap['gltf_pbr'] = gltf_remapKeys; 
        if self.support_openpbr:
            self.remapMap['open_pbr_surface'] = openpbr_remapKeys; 

    def getJSON(self) -> dict:
        ''' Get the JSON object representing the Physically Based Materials '''
        return self.materials
    
    def getJSONMaterialNames(self) -> list:
        ''' 
        Get the list of material names from the JSON object 
        @return The list of material names
        '''
        return self.materialNames
    
    def getMaterialXDocument(self) -> mx.Document:
        ''' 
        Get the MaterialX document 
        @return The MaterialX document
        '''
        return self.doc    

    def loadMaterialsFromFile(self, fileName) -> dict:
        ''' 
        @brief Load the Physically Based Materials from a JSON file 
        @param fileName The filename to load the JSON file from
        @return The JSON object representing the Physically Based Materials
        '''
        self.materials = None
        self.materialNames = []
        if not os.path.exists(fileName):
            self.logger.error(f'> File does not exist: {fileName}')
            return None

        with open(fileName, 'r') as json_file:
            self.materials = json.load(json_file)
            for mat in self.materials:
                self.materialNames.append(mat['name'])

        return self.materials
    
    def loadMaterialsFromString(self, matString) -> dict:
        ''' 
        @brief Load the Physically Based Materials from a JSON string 
        @param matString The JSON string to load the Physically Based Materials from
        @return The JSON object representing the Physically Based Materials
        '''
        self.materials = None
        self.materialNames = []
        self.materials = json.loads(matString)
        for mat in self.materials:
            self.materialNames.append(mat['name'])

        return self.materials

    def getMaterialsFromURL(self) -> dict:
        ''' 
        @brief Get the Physically Based Materials from the PhysicallyBased site 
        @return The JSON object representing the Physically Based Materials
        '''

        self.materials = None
        self.materialNames = []
        url = self.uri
        headers = {
            'Accept': 'application/json'
        }

        response = requests.get(url, headers=headers)

        if response.status_code == HTTPStatus.OK:
            self.materials = response.json()
            for mat in self.materials:
                self.materialNames.append(mat['name'])

        else:
            self.logger.error(f'> Status: {response.status_code}, {response.text}')

        return self.materials
    
    def printMaterials(self):
        '''
        @brief Print the materials to the console
        @return None
        '''
        for mat in self.materials:
            self.logger.info('Material name: ' + mat['name'])
            # Print out each key and value
            for key, value in mat.items():
                if (key != 'name' and value):
                    self.logger.info(f'>  - {key}: {value}')

    def writeJSONToFile(self, filename):
        '''
        @brief Write the materials to a JSON file
        @param filename The filename to write the JSON file to
        @return True if the file was written successfully, otherwise False
        '''
        if not self.materials:
            self.logger.warning('No materials to write')
            return False

        with open(filename, 'w') as json_file:
            json.dump(self.materials, json_file, indent=4)
            return True
        
        return False

    @staticmethod
    def skipLibraryElement(elem) -> bool:
        '''
        @brief Utility to skip library elements when iterating over elements in a document.
        @return True if the element is not in a library, otherwise False.
        '''
        return not elem.hasSourceUri()

    def _getMethodName(self):
        frame = inspect.currentframe().f_back
        method_name = frame.f_code.co_name
        return method_name
        #return inspect.currentframe().f_code.co_name

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

    def addComment(self, doc, commentString):
        '''
        @brief Add a comment to the MaterialX document
        @param doc The MaterialX document to add the comment to
        @param commentString The comment string to add
        @return None
        '''
        comment = doc.addChildOfCategory('comment')
        comment.setDocString(commentString)

    def convertToMaterialX(self, materialNames = [], shaderCategory='standard_surface',
                           remapKeys = {}, shaderPreFix ='') -> mx.Document:
        '''
        @brief Convert the Physically Based Materials to MaterialX format for a given target shading model.
        @param materialNames The list of material names to convert. If empty, all materials will be converted.
        @param shaderCategory The target shading model to convert to. Default is 'standard_surface'.
        @param remapKeys The remapping keys for the target shading model. If empty, the default remapping keys will be used.
        @param shaderPreFix The prefix to add to the shader name. Default is an empty string.
        @return The MaterialX document
        '''
        if not self.mx:
            self.logger.critical(f'> {self._getMethodName()}: MaterialX module is required')
            return None
        
        if not self.support_openpbr and shaderCategory == 'open_pbr_surface':
            self.logger.warning(f'> OpenPBR shading model not supported in MaterialX version {self.mx.getVersionString()}')
            return None

        if not self.materials:
            self.logger.info('> No materials to convert')
            return None            
        
        if len(remapKeys) == 0:
            remapKeys = self.getInputRemapping(shaderCategory)
            if len(remapKeys) == 0:
                self.logger.warning(f'> No remapping keys found for shading model: {shaderCategory}')

        # Create main document and import the library document
        self.doc = self.mx.createDocument()
        self.doc.importLibrary(self.stdlib)

        # Add header comments
        self.addComment(self.doc, 'Physically Based Materials from https://api.physicallybased.info ')
        self.addComment(self.doc, '  Processsed via API and converted to MaterialX ')  
        self.addComment(self.doc, '  Target Shading Model: ' + shaderCategory)  
        self.addComment(self.doc, '  Utility Author: Bernard Kwok. kwokcb@gmail.com ')  

        # Add properties to the material
        for mat in self.materials:
            matName = mat['name']

            # Filter by material name(s)
            if len(materialNames) > 0 and matName not in materialNames:
                #self.logger.debug('Skip material: ' + matName)
                continue            

            if (len(shaderPreFix) > 0):
                matName = matName + '_' + shaderPreFix 

            shaderName = self.doc.createValidChildName(matName + '_SHD_PBM')
            self.addComment(self.doc, ' Generated shader: ' + shaderName + ' ')         
            shaderNode = self.doc.addNode(shaderCategory, shaderName, self.mx.SURFACE_SHADER_TYPE_STRING)
            docString = mat['description']            
            refString = mat['reference']
            if len(refString) > 0:
                if len(docString) > 0:
                    docString += '. '
                docString += 'Reference: ' + refString[0]
            if len(docString) > 0:
                shaderNode.setDocString(docString)
            #shaderNode.addInputsFromNodeDef()
            #shaderNode.setAttribute(self.mx.InterfaceElement.NODE_DEF_ATTRIBUTE, nodedefString)

            # Create a new material
            materialName = self.doc.createValidChildName(matName + '_MAT_PBM')
            self.addComment(self.doc, ' Generated material: ' + materialName + ' ')         
            materialNode = self.doc.addNode(self.mx.SURFACE_MATERIAL_NODE_STRING, materialName, self.mx.MATERIAL_TYPE_STRING)
            shaderInput = materialNode.addInput(self.mx.SURFACE_SHADER_TYPE_STRING, self.mx.SURFACE_SHADER_TYPE_STRING)
            shaderInput.setAttribute(self.MTLX_NODE_NAME_ATTRIBUTE, shaderNode.getName())
            
            # Keys to skip.
            skipKeys = ['name', "density", "category", "description", "sources", "tags", "reference"]

            metallness = None
            roughness = None
            color = None
            transmission = None
            for key, value in mat.items():
                
                if (key not in skipKeys):
                    if key == 'metalness':
                        metallness = value
                    if key == 'roughness':
                        roughness = value
                    if key == 'transmission':
                        transmission = value
                    if key == 'color':
                        color = value

                    if key in remapKeys:
                        key = remapKeys[key]
                    input = shaderNode.addInputFromNodeDef(key)
                    if input:
                        # Convert number vector to string
                        if isinstance(value, list):
                            value = ','.join([str(x) for x in value])                        
                        # Convert number to string:
                        elif isinstance(value, (int, float)):
                            value = str(value)
                        input.setValueString(value)
                    #else:
                    #    self.logger.debug('Skip unsupported key: ' + key)

            if (transmission != None) and (metallness != None) and (roughness != None) and (color != None):
                if (metallness == 0) and (roughness == 0):
                    if 'transmission_color' in remapKeys:
                        key = remapKeys['transmission_color']
                        input = shaderNode.addInputFromNodeDef(key)
                        if input:
                            self.logger.debug(f'Set transmission color {key}: {color}')
                            value = ','.join([str(x) for x in color])                        
                            input.setValueString(value)

        return self.doc
    
    def writeMaterialXToFile(self, filename):
        ''' 
        @brief Write the MaterialX document to disk 
        @param filename The filename to write the MaterialX document to
        @return None
        '''
        if not self.mx:
            self.logger.critical(f'> {self._getMethodName()}: MaterialX module is required')
            return

        writeOptions = self.mx.XmlWriteOptions()
        writeOptions.writeXIncludeEnable = False
        writeOptions.elementPredicate = self.skipLibraryElement        
        self.mx.writeToXmlFile(self.doc, filename, writeOptions)

    def convertToMaterialXString(self):
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
        mtlx = self.mx.writeToXmlString(self.doc, writeOptions)
        return mtlx
