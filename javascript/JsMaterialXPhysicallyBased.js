let MTLX_NODE_NAME_ATTRIBUTE = 'nodename';

/**
 * @class JsPhysicallyBasedMaterialLoader
 * @brief Javascript class for querying materials from the Physically Based database
 * and creating MaterialX materials.
 */
class JsPhysicallyBasedMaterialLoader {
    /**
     * @var url 
     * @brief URL to fetch the Physically Based Materials
     */
    url = '';
    /**
     * @var headers 
     * @brief Headers for the fetch operation
     */
    headers = {};
    /**
     * @var materials 
     * @brief List of Physically Based Materials
     */
    materials = null;
    /** 
     * @var materialNames 
     * @brief List of Physically Based Material names
     */
    materialNames = [];
    /**
     * @var mxMaterialNames 
     * @brief List of MaterialX Material names
     */
    mxMaterialNames = [];
    /** 
     * @var mx 
     * @brief MaterialX module
     */
    mx = null;
    /**
     * @var doc 
     * @brief Working MaterialX document
     */
    doc = null;
    /**
     * @var stdlib 
     * @brief MaterialX standard libraries
     */
    stdlib = null;
    /** 
     * @var remapMap 
     * @brief Remap keys for input values for different shading models
     */
    remapMap = {};

    /**
     * @brief
     * Constructor for the PhysicallyBasedMaterialLoader
     * @returns {void}
     */
    constructor(mtlx_module = null, mtlx_stdlib = null) 
    {
        this.url = 'https://api.physicallybased.info/materials';
        this.headers = { 'Accept': 'application/json' };

        this.materials = null;
        this.materialNames = [];

        this.mxMaterialNames = [];
        this.mx = null;
        if (mtlx_module) {
            this.mx = mtlx_module;
        }
        this.stdlib = null;
        if (mtlx_stdlib) {
            this.stdlib = mtlx_stdlib;
        }
        this.doc = null;

        this.initializeInputRemapping();
    }

    /**
     * Get the Physically Based Materials as JSON
     * @returns {object[]} - List of Physically Based Materials
     */
    getJSON() 
    {
        return this.materials
    }

    /**
     * Get list of the Physically Based Material names
     */
    getJSONMaterialNames()
    {
        return this.materialNames
    }

    /**
     * Get the MaterialX document
     */
    getMaterialXDocument() 
    {
        return this.doc;
    }

    /**
     * Validate the MaterialX document
     * @returns {[boolean, errors]} - True if the document is valid. False otherwise
     */
    validateDocument() 
    {
        if (this.doc) {
            let errors = {}
            let errorString = ''
            var valid = this.doc.validate(errors);
            if (!valid) {
                errorString = errors.message;
            }
            return [valid, errorString]
        }
        return [false, 'No MaterialX document'];
    }

    /**
     * Get the remapping keys for a given shading model
     * @param shadingModel - Shading model to get the remapping keys
     * @returns Remapping keys for the shading model. Empty object if not found
     */
    getInputRemapping(shadingModel) 
    {
        if (shadingModel in this.remapMap) {
            return this.remapMap[shadingModel];
        }
        return {};
    }

    /**
     * Set the default remapping keys for different shading models : glTF, OpenPBR, and Autodesk Standard Surface
     * @returns {void}
     */
    setDefaultRemapKeys() 
    {
        const standard_surface_remapKeys = {
            "color": "base_color",
            "specularColor": "specular_color",
            "roughness": "specular_roughness",
            "metalness": "metalness",
            "ior": "specular_IOR",
            "subsurfaceRadius": "subsurface_radius",
            "transmission": "transmission",
            "transmission_color": "transmission_color",
            "transmissionDispersion": "transmission_dispersion",
            "thinFilmThickness": "thin_film_thickness",
            "thinFilmIor": "thin_film_IOR"
        };

        const openpbr_remapKeys = {
            "color": "base_color",
            "specularColor": "specular_color",
            "roughness": "specular_roughness",
            "metalness": "base_metalness",
            "ior": "specular_ior",
            "subsurfaceRadius": "subsurface_radius",
            "transmission": "transmission_weight",
            "transmission_color": "transmission_color",
            "transmissionDispersion": "transmission_dispersion_abbe_number",
            "thinFilmThickness": "thin_film_thickness",
            "thinFilmIor": "thin_film_ior"
        };

        const gltf_remapKeys = {
            "color": "base_color",
            "specularColor": "specular_color",
            "roughness": "roughness",
            "metalness": "metallic",
            "ior": "ior",
            "transmission": "transmission",
            "transmission_color": "attenuation_color",
            "thinFilmThickness": "iridescence_thickness",
            "thinFilmIor": "iridescence_ior"
        };

        this.remapMap = {
            'standard_surface': standard_surface_remapKeys,
            'gltf_pbr': gltf_remapKeys,
            'open_pbr_surface': openpbr_remapKeys
        };
    }


    /**
     * Initialize the input remapping for different shading models
     * @returns {void}
     */
    initializeInputRemapping() 
    {
        console.log('Initializing input remapping for Physically Based Materials...');
        this.remapMap = null;

        const remapKeyURL = 'https://raw.githubusercontent.com/kwokcb/materialxMaterials/refs/heads/main/src/materialxMaterials/data/PhysicallyBasedMaterialX/PhysicallyBasedToMtlxMappings.json';

        fetch(remapKeyURL)
            .then((response) => 
            {
                if (!response.ok) {
                    console.warn(`HTTP error! Status: ${response.status}`);
                    return null;
        }
                return response.json();
            })
            .then((data) => {
                if (data) {
                    this.remapMap = data;
                    console.log('- Remap keys loaded from repo:', this.remapMap);
                } else {
                    console.warn('- No remap keys from repo. Using default remap keys.');
                    this.setDefaultRemapKeys();
        }
            })
            .catch((error) => {
                console.log('- Error loading remap keys:', error);
                this.setDefaultRemapKeys();
                console.warn('- Using default remap keys.', this.remapMap);
            });
    }

    /**
     * Load the MaterialX module
     * @returns {Promise} - Promise to load the MaterialX module
     */
    loadMaterialX() 
    {
        return new Promise((resolve, reject) => {
            MaterialX().then((mtlx) => {
                this.mx = mtlx;
                resolve();
            }).catch((error) => {
                reject(error);
            });
        });
    }

    /**
     * Get the Physically Based Materials from the API
     * @returns {object[]} - List of Physically Based Materials in JSON format
     */
    async getPhysicallyBasedMaterials() 
    {
        try {
            this.materials = null
            this.materialNames = [];

            const response = await fetch(this.url, {
                method: 'GET',
                headers: this.headers
            });

            if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
            }

            this.materials = await response.json();
            for (let i = 0; i < this.materials.length; i++) {
                this.materialNames.push(this.materials[i]['name']);
            }
            return this.materials;
        } catch (error) {
            console.error('There has been a problem with your fetch operation:', error);
        }

        return null;
    }

    /**
     * Load the MaterialX standard libraries
     * @returns {void}
     */
    loadStandardLibraries() 
    {
        if (!this.mx) {
            // Call the asynchronous function and then perform additional logic
            this.loadMaterialX().then(() => {

                this.esslgenerator = new this.mx.EsslShaderGenerator();
                this.esslgenContext = new this.mx.GenContext(this.esslgenerator);
                this.stdlib = this.mx.loadStandardLibraries(this.esslgenContext);
                let children = this.stdlib.getChildren();
                for (let i = 0; i < children.length; i++) {
                    let child = children[i];
                    child.setSourceUri('STDLIB_ELEMENT');
                }

                console.log("MaterialX is loaded");
            }).catch((error) => {
                console.error("Error loading MaterialX:", error);
            });
        }
    }

    /**
     * Predicate to skip library elements
     * @param element - MaterialX element
     * @returns True if the element is a library element. False otherwise
     */
    skipLibraryElement(element) 
    {
        return !elem.hasSourceUri()
    }

    /**
     * Get the MaterialX document as a string
     * @returns {string} - MaterialX document as a string. Empty string if no document
     */
    getMaterialXString() 
    {
        if (!this.doc) {
            console.error('No MaterialX document to convert');
            return '';
        }

        // Create write options
        const writeOptions = new this.mx.XmlWriteOptions();
        writeOptions.writeXIncludeEnable = false;
        //writeOptions.writeXIncludes = false;
        writeOptions.elementPredicate = this.skipLibraryElement;

        // Convert the MaterialX document to a string
        const mtlx = this.mx.writeToXmlString(this.doc, writeOptions);
        return mtlx;
    }

    /** 
     * Add a comment to the MaterialX document
     * @param doc - MaterialX document
     * @param commentString - Comment string to add
     */
    addComment(doc, commentString) 
    {
        let comment = doc.addChildOfCategory('comment')
        comment.setDocString(commentString)
    }


    /**
     * @brief Convert the Physically Based Materials to MaterialX
     * @param shaderCategory - MaterialX shader category
     * @param addAllInputs - Add all inputs from node definitions
     * @param materialNames - List of material names to convert. If empty all materials are converted
     * @param remapKeys - Remap keys to MaterialX shader inputs. If not specified the default remap keys are used if any.
     * @param shaderPreFix - Prefix for the shader name. Default is empty
     * @param references - List of references found. (returned). Each reference is a object: { name: string, reference: string } 
     * @returns True if the conversion is successful. False otherwise
     */
    convertToMaterialX(shaderCategory, references, addAllInputs = false, materialNames = [], remapKeys = {}, shaderPreFix = '') 
    {
        if (!this.mx) {
            console.error('MaterialX module is not loaded');
            return false;
        }

        if (!this.materials) {
            console.warn('No Physically Based Materials to convert');
            return false;
        }

        if (remapKeys.length == 0) {
            remapKeys = this.getInputRemapping(shaderCategory);
        }

        // Create a dummy doc with the surface shader with all inputs
        // as reference
        let refDoc = this.mx.createDocument();
        refDoc.importLibrary(this.stdlib);
        const refNode = refDoc.addNode(shaderCategory, 'refShader', this.mx.SURFACE_SHADER_TYPE_STRING);
        //refNode.addInputsFromNodeDef() -- This is missing from the JS API.
        this.doc = this.mx.createDocument();

        // Add document level accreditation
        let docString = 'Physically Based Materials from https://api.physicallybased.info.\n'
        docString += '  Content Author: Anton Palmqvist, https://antonpalmqvist.com/ \n'
        docString += `  Content processsed via REST API and mapped to MaterialX V${this.mx.getVersionString()} \n`
        docString +=  `  Target Shading Model: ${shaderCategory} \n`
        docString +=  '  Utility Author: Bernard Kwok. kwokcb@gmail.com '  
        this.doc.setDocString(docString);

        // Add properties to the material
        for (let i = 0; i < this.materials.length; i++) {
            const mat = this.materials[i];
            let matName = mat['name'];

            // Filter by material name(s)
            if (materialNames.length > 0 && !materialNames.includes(matName)) {
                // Skip material
                console.log('Skipping material:', matName);
                continue;
            }


            if (shaderPreFix.length > 0) {
                matName = shaderPreFix + '_' + matName;
            }

            const shaderName = this.doc.createValidChildName('SPB_' + matName + '_' + shaderCategory);
            this.addComment(this.doc, ' Generated shader: ' + matName + ' ');
            const shaderNode = this.doc.addNode(shaderCategory, shaderName, this.mx.SURFACE_SHADER_TYPE_STRING);

            const category = mat['category'];
            const group = mat['group'];
            let uifolder = '';
            if (category && category.length > 0) {
                uifolder = category[0];
            }
            if (group && group.length > 0) {
                if (uifolder.length > 0) {
                    uifolder += '/';
                }
                uifolder += group[0];
            }
            if (uifolder.length > 0) {
                shaderNode.setAttribute('uifolder', uifolder);
            }

            let docString = ''
            if (mat['description'].length > 0) {
                docString += 'Description: ' + mat['description'];
            }
            const refString = mat['reference'];
            if (refString.length > 0) {
                if (docString.length > 0) {
                    docString += '. ';
                }
                docString += 'Reference: ' + refString[0];

                let referenceItem = { name: matName, reference: refString[0] };
                console.log('Add Reference:', referenceItem);
                references.push(referenceItem);
            }
            if (docString.length > 0) {
                shaderNode.setDocString(docString);
            }

            // Create a new material
            const materialName = this.doc.createValidChildName('MPB_' + matName + '_' + shaderCategory);
            this.addComment(this.doc, ' Generated material: ' + matName + ' ');
            const materialNode = this.doc.addNode(this.mx.SURFACE_MATERIAL_NODE_STRING, materialName, this.mx.MATERIAL_TYPE_STRING);
            const shaderInput = materialNode.addInput(this.mx.SURFACE_SHADER_TYPE_STRING, this.mx.SURFACE_SHADER_TYPE_STRING);
            shaderInput.setAttribute(MTLX_NODE_NAME_ATTRIBUTE, shaderNode.getName());

            // Warning this is a bit bespoke for remapping keys
            // to Autodesk Standard Surface shader inputs
            const skipKeys = ['name', "density", "category", "description", "sources", "tags", "reference"];

            let metallness = null;
            let roughness = null;
            let transmission_color = null;
            let transmission = null;
            Object.entries(mat).forEach(([key, value]) => {

                if (!skipKeys.includes(key)) {

                    if (key == 'metalness') {
                        metallness = value;
                        //console.log('Metalness:', metallness);
                    }
                    if (key == 'roughness') {
                        roughness = value;
                        //console.log('Roughness:', roughness);
                    }
                    if (key == 'transmission') {
                        transmission = value;
                        //console.log('Transmission:', transmission);
                    }
                    if (key == 'color') {
                        transmission_color = value;
                        //console.log('Color:', color);
                    }    

                    if (remapKeys[key]) {
                        key = remapKeys[key];
                    }

                    let refInput = refNode.getInput(key);
                    if (!refInput)
                        refInput = refNode.addInputFromNodeDef(key);
                    if (refInput) {
                        const input = shaderNode.addInput(key);
                        input.copyContentFrom(refInput);
                        if (input) {
                            // Convert number vector to string
                            if (Array.isArray(value)) {
                                value = value.join(',');
                            }
                            // Convert number to string
                            else if (typeof value === 'number') {
                                value = value.toString();
                            }
                            // Note: This API has side-effects as the
                            // type is set to "string" when the value is set. Thus
                            // we must explicitly set the type here.
                            input.setValueString(value, refInput.getType());
                        }
                    }
                    else {
                        //console.log('>>> Cannot create input:', key)
                    }
                }
            });

            if (transmission !== null && metallness !== null && roughness !== null && transmission_color !== null) 
            {
                if (metallness == 0 && roughness == 0) 
                {
                    if (remapKeys['transmission_color']) {
                        let inputName = remapKeys['transmission_color'];
                        let input = shaderNode.addInput(inputName);
                        if (input) {
                            let value = transmission_color.join(',');
                            //console.log(`Add "${inputName}": "${value}"`);
                            input.setValueString(value, 'color3');
                        }
                    }
                }
            };                
        }
        return true;
    }

}
