'''
@brief Class to load Physically Based Materials from the PhysicallyBased site.
and convert the materials to MaterialX format for given target shading models.
'''

import requests, json, os, inspect # type: ignore
import logging as lg 
from http import HTTPStatus
import MaterialX as mx # type: ignore
from typing import Optional
import importlib.resources
import json

class PhysicallyBasedMaterialLoader:
    '''
    @brief Class to load Physically Based Materials from the PhysicallyBased site.
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
        ### Logger
        self.logger = lg.getLogger('PBMXLoader')
        lg.basicConfig(level=lg.INFO)

        ### Materials list
        self.materials : dict = {}
        ### Material names
        self.materialNames : list[str]= []
        ### Root URI for the PhysicallyBased site
        self.uri = 'https://api.physicallybased.info/materials'
        ### MaterialX document used for conversion
        self.doc = None
        ### MaterialX module
        self.mx = mx_module
        ### MaterialX standard library
        self.stdlib = mx_stdlib
        ### MaterialX node name attribute
        self.MTLX_NODE_NAME_ATTRIBUTE = 'nodename'
        ### OpenPBR support flag
        self.support_openpbr = False
        ### Remapping keys for different shading models
        self.remapMap = {}
        ### Default remapping file (part of installed package)
        self.remapFile = 'PhysicallyBasedMaterialX/PhysicallyBasedToMtlxMappings.json'

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
        See: https://api.physicallybased.info/operations/get-materials
        for more information on material properties.

        The JSON file PhysicallyBasedToMtlxMappings.json which is part of the package
        will be used if it exists. Otherwise, default remapping keys will be used.

        The currently supported shading models are:
        - standard_surface
        - open_pbr_surface
        - gltf_pbr
        @return None
        '''
        # Read PhysicallyBasedToMtlxMappings.json installed package
        self.remapMap = {}

        try:
            with importlib.resources.files("materialxMaterials.data").joinpath(self.remapFile).open("r", encoding="utf-8") as json_file:
                self.logger.info(f'> Load remapping from installed package: {self.remapFile}')
                self.remapMap = json.load(json_file)
        except FileNotFoundError:
            self.logger.warn('> No remapping file found in installed package. Using default remapping keys.')

        if self.remapMap:
            return
    
        # Remap keys for Autodesk Standard Surface shading model. 
        standard_surface_remapKeys = {
            'color': 'base_color',
            'specularColor': 'specular_color',
            'roughness': 'specular_roughness',
            'metalness': 'metalness',
            'ior': 'specular_IOR',
            'subsurfaceRadius': 'subsurface_radius',
            'transmission': 'transmission',
            'transmission_color': 'transmission_color', # 'color' remapping as needed 
            'transmissionDispersion' : 'transmission_dispersion',
            'thinFilmThickness' : 'thin_film_thickness',            
            'thinFilmIor' : 'thin_film_IOR',
        }
        # Remap keys for OpenPBR shading model.
        # Q: When to set geometry_thin_walled to true?
        openpbr_remapKeys = {
            'color': 'base_color',
            'specularColor': 'specular_color',
            'roughness': 'specular_roughness', # 'base_diffuse_roughness',
            'metalness': 'base_metalness',
            'ior': 'specular_ior',
            'subsurfaceRadius': 'subsurface_radius',
            'transmission': 'transmission_weight',
            'transmission_color': 'transmission_color', # 'color' remapping as needed 
            'transmissionDispersion': 'transmission_dispersion_abbe_number',
            #'complexIor' TODO : add in array remap 
            # Complex IOR values, n (refractive index), and k (extinction coefficient), for each color channel, in the following order:
            #   nR, kR, nG, kG, nB, kB. 
            'thinFilmThickness' : 'thin_film_thickness',
            'thinFilmIor' : 'thin_film_ior',
        }
        # Remap keys for Khronos glTF shading model.
        gltf_remapKeys = {
            'color': 'base_color',
            'specularColor': 'specular_color',
            'roughness': 'roughness',
            'metalness': 'metallic',
            'ior': 'ior',
            'transmission': 'transmission',
            'transmission_color': 'attenuation_color', # Remap transmission color to attenuation color
            'thinFilmThickness' : 'iridescence_thickness',
            'thinFilmIor' : 'iridescence_ior',
        }

        self.remapMap = {}
        self.remapMap['standard_surface'] = standard_surface_remapKeys; 
        self.remapMap['gltf_pbr'] = gltf_remapKeys; 
        if self.support_openpbr:
            self.remapMap['open_pbr_surface'] = openpbr_remapKeys; 

    def writeRemappingFile(self, filepath):
        '''
        @brief Write the remapping keys to a JSON file.
        @param filepath The filename to write the remapping keys to.
        @return None
        '''
        if not self.remapMap:
            self.logger.warning('No remapping keys to write')
            return
                
        with open(filepath, 'w') as json_file:
            json.dump(self.remapMap, json_file, indent=4)

    def readRemappingFile(self, filepath):
        '''
        @brief Read the remapping keys from a JSON file.
        @param filepath The filename to read the remapping keys from.
        @return A dictionary of remapping keys.
        '''
        if not os.path.exists(filepath):
            self.logger.error(f'> File does not exist: {filepath}')
            return {}

        with open(filepath, 'r') as json_file:
            self.remapMap = json.load(json_file)

        return self.remapMap

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
        self.materials.clear()
        self.materialNames.clear()
        if not os.path.exists(fileName):
            self.logger.error(f'> File does not exist: {fileName}')
            return {}

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
        self.materials.clear()
        self.materialNames.clear()
        self.materials = json.loads(matString)
        for mat in self.materials:
            self.materialNames.append(mat['name'])

        return self.materials

    def getMaterialsFromURL(self) -> dict:
        ''' 
        @brief Get the Physically Based Materials from the PhysicallyBased site 
        @return The JSON object representing the Physically Based Materials
        '''

        self.materials.clear()
        self.materialNames.clear()
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
        '''
        @brief Get the name of the calling method for logging purposes.
        @return The name of the calling method.
        '''
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

    def _map_keys_to_definition(self, mat, ndef):
        '''
        @brief Map a key to a NodeDef input
        @param mat Material to map keys from
        @param ndef The definition to map the key to
        @return The input name if the key was mapped, otherwise None
        '''
        for key, value in mat.items():
            uifolder = None
            if ndef.getInput(key) is None:
                if key == 'name':
                    # Skip as these wil be node instance names
                    pass 
                    #continue

                print('Add key to nodedef:', key)

                self.logger.debug(f'> Add key as input: {key}')
                
                input_type = "string"
                if 'color' in key.lower():
                    input_type = "color3"
                    value = "1,1,1"
                elif isinstance(value, float):
                    input_type = "float"
                    value = "0.0"
                elif isinstance(value, int):
                    input_type = "float"
                    value = "0.0"
                elif key == 'category':
                    #if isinstance(value, list) and len(value) > 0:                            
                    #    uifolder = str(value[0])
                    #else:
                    #    uifolder = str(value)
                    #value = None
                    pass
                elif key in ['sources', 'reference', 'tags', 'group']:
                    value = ''

                input = ndef.addInput(key, input_type)
                if input:
                    if value is not None:
                        if isinstance(value, list):
                            # Split list into array
                            value_list = [str(x) for x in value]
                            # Check if values are numbers
                            is_number_list = all(isinstance(x, (int, float)) for x in value)
                            if is_number_list:
                                if len(value_list) > 4 :
                                    input.setType('string') # floatarray will cause errors in shader generation ! 
                                elif len(value_list) > 3 :
                                    input.setType('vector4')
                                elif len(value_list) > 2 :
                                    input.setType('vector3')
                                elif len(value_list) > 1 :
                                    input.setType('vector2')
                                else:
                                    input.setType('float')    
                                # Replace all numbers with 0.0
                                value_list = ['0.0' for x in value_list]
                            value = ', '.join(value_list)

                            #value = ','.join([str(x) for x in value])
                        input.setValueString(str(value))


                    uiname = key
                    # Split camel case names and separate by space
                    # e.g. specularColor -> Specular Color
                    uiname = ''.join([' ' + c if c.isupper() else c for c in key]).strip().title() 
                    input.setAttribute("uiname", uiname)

                    uifolder = 'Base'
                    if key in ['description', 'sources', 'reference', 'tags']:
                        uifolder = 'Metadata'
                    input.setAttribute("uifolder", uifolder)

                    # Add doc string
                    doc_string = ''
                    if key == 'description':
                        print('set doc string to', value)
                        doc_string = str(value)
                    if len(doc_string) > 0:
                        input.setDocString(doc_string)

                    if uifolder is not None:
                        input.setAttribute("uifolder", uifolder)

    def createNodeDef(self):
        '''
        @brief Create a NodeDef for the Physically Based Material inputs
        @return The MaterialX document containing the NodeDef
        @details The NodeDef will contain inputs for all the keys in the Physically Based Material JSON object.

        The nodegraph is a placeholder with a simple diffuse shader accepting color as followe:
        <pre>
          <nodegraph name="NG_PhysicallyBasedMaterial" nodedef="ND_PhysicallyBasedMaterial">
            <oren_nayar_diffuse_bsdf name="oren_nayar_diffuse_bsdf" type="BSDF" >
                <output name="out" type="BSDF" />
                <input name="color" type="color3" interfacename="color" />
                <input name="roughness" type="color3" interfacename="roughness" />
            </oren_nayar_diffuse_bsdf>
            
            <surface name="surface" type="surfaceshader">
                <input name="bsdf" type="BSDF" output="out" nodename="oren_nayar_diffuse_bsdf" />
            </surface>    
            
            <output name="out" type="surfaceshader" nodename="surface"/>
          </nodegraph>
        </pre>
        '''
        doc = mx.createDocument()

        # Create placeholder nodegraph
        graph = doc.addNodeGraph("NG_PhysicallyBasedMaterial")
        graph.setNodeDefString('ND_PhysicallyBasedMaterial')

        node = graph.addNode('oren_nayar_diffuse_bsdf', 'oren_nayar_diffuse_bsdf', 'BSDF')
        node_in = node.addInput('color', 'color3')
        node_in.setInterfaceName('color')
        node_in_rough = node.addInput('roughness', 'float')
        node_in_rough.setInterfaceName('roughness')
        node.addOutput('out', 'BSDF')

        node = graph.addNode('surface', 'surface', 'surfaceshader')
        node_in = node.addInput('bsdf', 'BSDF')
        node_in.setAttribute('out', 'out')
        node_in.setNodeName('oren_nayar_diffuse_bsdf')

        node_out = graph.addOutput('out', 'surfaceshader')
        node_out.setNodeName('surface')

        # Create definition template
        ndef = doc.addNodeDef("ND_PhysicallyBasedMaterial", 'surfaceshader')
        #graph.removeOutput('out')
        ndef.setNodeString('physbased_pbr_surface')
        ndef.setNodeGroup("pbr")
        ndef.setDocString("NodeDef for Physically Based Material inputs")
        ndef.setVersionString("1.0")
        ndef.setAttribute("isdefaultversion", "true")

        for mat in self.materials:
            # Map keys to definition inputs
            self._map_keys_to_definition(mat, ndef)

        doc_mat = mx.createDocument()
        doc_mat.copyContentFrom(doc)
        for mat in self.materials:
            matName = mat['name']
            shaderName = doc_mat.createValidChildName(matName + '_SHD_PBM')
            shaderNode = doc_mat.addNode('physbased_pbr_surface', shaderName, mx.SURFACE_SHADER_TYPE_STRING)
            for key, value in mat.items():
                if key == 'name':
                    new_name = doc_mat.createValidChildName(str(value))
                    shaderNode.setName(new_name)

                input = shaderNode.addInputFromNodeDef(key)
                if value is not None:
                    if isinstance(value, list):
                        # Split list into array
                        value_list = [str(x) for x in value]
                        # Check if values are numbers
                        is_number_list = all(isinstance(x, (int, float)) for x in value)
                        if is_number_list:
                            value = ', '.join(value_list)
                    input.setValueString(str(value))     

                    # Add doc string
                    doc_string = ''
                    if key == 'description':
                        doc_string = str(value)
                    if len(doc_string) > 0:
                        print('set doc string to', value)
                        shaderNode.setDocString(doc_string)
           
            shaderNode.setAttribute('uiname', matName)

            # Create a new material
            materialName = doc_mat.createValidChildName(matName + '_MAT_PBM')
            materialNode = doc_mat.addNode(mx.SURFACE_MATERIAL_NODE_STRING, materialName, mx.MATERIAL_TYPE_STRING)
            shaderInput = materialNode.addInput(mx.SURFACE_SHADER_TYPE_STRING, mx.SURFACE_SHADER_TYPE_STRING)
            shaderInput.setAttribute(self.MTLX_NODE_NAME_ATTRIBUTE, shaderNode.getName())

        return doc, doc_mat

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
        if not self.doc:
            return None

        self.doc.importLibrary(self.stdlib)

        # Add header comments
        self.addComment(self.doc, 'Physically Based Materials from https://api.physicallybased.info ')
        self.addComment(self.doc, '  Content Author: Anton Palmqvist, https://antonpalmqvist.com/ ')
        self.addComment(self.doc, f'  Content processsed via REST API and mapped to MaterialX V{self.mx.getVersionString()} ')
        self.addComment(self.doc, f'  Target Shading Model: {shaderCategory} ')  
        self.addComment(self.doc, '  Utility Author: Bernard Kwok. kwokcb@gmail.com ')  

        # Add properties to the material
        for mat in self.materials:
            matName = mat['name']
            uiName = matName

            # Filter by material name(s)
            if len(materialNames) > 0 and matName not in materialNames:
                #self.logger.debug('Skip material: ' + matName)
                continue            

            if (len(shaderPreFix) > 0):
                matName = matName + '_' + shaderPreFix 

            shaderName = self.doc.createValidChildName(matName + '_SHD_PBM')
            self.addComment(self.doc, ' Generated shader: ' + shaderName + ' ')         
            shaderNode = self.doc.addNode(shaderCategory, shaderName, self.mx.SURFACE_SHADER_TYPE_STRING)
            shaderNode.setAttribute('uiname', uiName)

            folderString = ''
            if 'category' in mat:
                folderString = mat['category'][0]
            if 'group' in mat:
                if len(folderString) > 0:
                    folderString += '/'
                    folderString += mat['group']
            if len(folderString) > 0:
                shaderNode.setAttribute("uifolder", folderString)

            docString = mat['description']            
            refString = mat['reference']
            if len(refString) > 0:
                if len(docString) > 0:
                    docString += '. '
                docString += 'Reference: ' + refString[0]
            if len(docString) > 0:
                shaderNode.setDocString(docString)
            
            # TODO: Add in option to add all inputs + add nodedef string
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
                    # Keep track of these for possible transmission color remapping
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
                    else:
                        self.logger.debug('Skip unsupported key: ' + key)

            # Re-route color to mapped transmission_color if needed
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
