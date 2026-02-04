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

        this.physlib = null;
        // PhysicallyBased MaterialX surface definition name
        this.physlib_definition_name = "ND_PhysicallyBasedMaterial";
        // PhysicallyBased MaterialX surface implementation (nodegraph) name
        this.physlib_implementation_name = "NG_PhysicallyBasedMaterial";
        // PhysicallyBased MaterialX surface category
        this.physlib_category = "physbased_pbr_surface"
        // Document containing PhysicallyBased materials using PhysicallyBasedMaterial definition
        this.physlib_materials = null
        // Document containing PhysicallyBased MaterialX translators
        this.physlib_translators = null
        // All MaterialX definitions (standard library + PhysicallyBased definition + translators)
        this.all_lib = null;
        // Translated materials keyed by shading model
        this.translated_materials = {};
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
        else
        {
            console.log('>> No remap keys for shading model:', shadingModel);
        }
        return {};
    }

    /**
     * Get remmapping map
     * @returns {object} - Remapping map
     */
    getInputRemappingMap() 
    {
        return this.remapMap;
    }

    get_physlib() {
        // Get the Physically Based MaterialX definition library.
        return this.physlib;
    }

    get_physlib_definition() {
        // Get the Physically Based MaterialX definition NodeDef.
        if (this.physlib) {
            return this.physlib.getNodeDef(this.get_physlib_definition_name());
        }
        return null;
    }

    get_physlib_category() {
        // Get the Physically Based MaterialX surface category.
        return this.physlib_category;
    }

    get_physlib_definition_name() {
        // Get the Physically Based MaterialX definition name.
        return this.physlib_definition_name;
    }

    get_physlib_implementation_name() {
        // Get the Physically Based MaterialX implementation (nodegraph) name.
        return this.physlib_implementation_name;
    }

    get_physlib_materials() {
        // Get the Physically Based MaterialX materials document.
        return this.physlib_materials;
    }

    get_definitions() {
        // Get a combined MaterialX document containing the standard library and Physically Based MaterialX definition and translators.
        if (!this.all_lib) {
            this.all_lib = this.mx.createDocument();
            this.all_lib.copyContentFrom(this.stdlib);
            if (this.physlib) {
                this.all_lib.copyContentFrom(this.physlib);
            }
            if (this.physlib_translators) {
                this.all_lib.copyContentFrom(this.physlib_translators);
            }
        }
        return this.all_lib;
    }

    map_keys_to_definition(mat, ndef) {
        // Map a key to a NodeDef input
        for (let [key, value] of Object.entries(mat)) {
            let uifolder = null;
            if (!ndef.getInput(key)) {
                //if (key === 'name') {
                    // Skip as these will be node instance names
                //    continue;
                //}

                let input_type = "string";
                if (key.toLowerCase().includes('color')) {
                    input_type = "color3";
                    value = "1,1,1";
                } else if (typeof value === 'number' && !Number.isInteger(value)) {
                    input_type = "float";
                    value = "0.0";
                } else if (typeof value === 'number' && Number.isInteger(value)) {
                    input_type = "float";
                    value = "0.0";
                } else if (key === 'category') {
                    // category handling (optional)
                } else if (["sources", "reference", "tags", "group"].includes(key)) {
                    value = '';
                }
                //console.log(`> Add key as input: ${key}. Type: ${typeof value}. input_type: ${input_type}, value: ${value}`);
                let input = ndef.addInput(key, input_type);
                if (input) {
                    if (value !== undefined && value !== null) {
                        if (Array.isArray(value)) {
                            let value_list = value.map(x => String(x));
                            let is_number_list = value.every(x => typeof x === 'number');
                            if (is_number_list) {
                                if (value_list.length > 4) {
                                    input_type = 'string'; // floatarray will cause errors in shader generation!
                                } else if (value_list.length > 3) {
                                    input_type = 'vector4';
                                } else if (value_list.length > 2) {
                                    input_type = 'vector3';
                                } else if (value_list.length > 1) {
                                    input_type = 'vector2';
                                } else {
                                    input_type = 'float';
                                }
                                value_list = value_list.map(() => '0.0');
                            }
                            value = value_list.join(', ');
                        }
                        input.setValueString(String(value));
                        input.setType(input_type);
                    }
                    // Split camel case names and separate by space, e.g. specularColor -> Specular Color
                    let uiname = key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase()).trim();
                    input.setAttribute("uiname", uiname);
                    uifolder = 'Base';
                    if (["description", "sources", "reference", "tags"].includes(key)) {
                        uifolder = 'Metadata';
                    }
                    input.setAttribute("uifolder", uifolder);
                }
            }
        }
    }

    find_all_bxdf(doc) {
        // Scan all nodedefs with output type of "surfaceshader"
        let bxdfs = [];
        for (let nodedef of doc.getNodeDefs()) {
            if (nodedef.getType() === "surfaceshader") {
                if (nodedef.getNodeString() !== "convert" && nodedef.getNodeString() !== "surface" && nodedef.getNodeGroup() === "pbr") {
                    bxdfs.push(nodedef);
                }
            }
        }
        return bxdfs;
    }

    derive_translator_name_from_targets(source, target )
    {
        return `ND_${source}_to_${target}`;
    }

    create_translator(doc, source, target, source_version = "", target_version = "", mappings = null, output_doc) {
        /**
         * Create a translator nodedef and nodegraph from source to target definitions.
         * @param {object} doc - The source document containing the definition.
         * @param {string} source - The source definition category.
         * @param {string} target - The target definition category.
         * @param {string} source_version - The source version string. If empty, use the first source definition version found.
         * @param {string} target_version - The target version string. If empty, use the first target definition version found.
         * @param {object} mappings - A dictionary mapping source input names to target input names.
         * @param {object} output_doc - The document to add the translator to. If null, use the source doc.
         * @returns {object|null} The created translator definition.
         */
        if (!output_doc) {
            return null;
        }
        // Get source and target nodedefs
        let nodedefs = this.find_all_bxdf(doc);
        let source_nodedef = null;
        let target_nodedef = null;
        for (let nodedef of nodedefs) {
            if (nodedef.getNodeString() === source) {
                if (source_version === "" || nodedef.getVersionString() === source_version) {
                    source_nodedef = nodedef;
                }
            }
            if (nodedef.getNodeString() === target) {
                if (target_version === "" || nodedef.getVersionString() === target_version) {
                    target_nodedef = nodedef;
                }
            }
        }
        if (!source_nodedef || !target_nodedef) {
            if (!source_nodedef) {
                console.warn(`Source nodedef not found for '${source}' with version '${source_version}'`);
            }
            if (!target_nodedef) {
                console.warn(`Target nodedef not found for '${target}' with version '${target_version}'`);
            }
            return null;
        }
        //console.log('******* Source nodedef:\n', this.mx.prettyPrint(source_nodedef));

        // 1. Add a new nodedef for the translator
        let derived_name = this.derive_translator_name_from_targets(source, target);
        let nodename = derived_name.startsWith("ND_") ? derived_name.substring(3) : derived_name;
        let translator_nodedef = output_doc.getNodeDef(derived_name);
        if (translator_nodedef) {
            console.log(`> Translator NodeDef already exists: ${target_nodedef.getName()}`);
            return translator_nodedef;
        }
        else {
            console.log(`> Creating Translator NodeDef: ${nodename} from '${source}' to '${target}'`);
        }

        translator_nodedef = output_doc.addNodeDef(derived_name);
        translator_nodedef.removeOutput("out");
        translator_nodedef.setNodeString(nodename);
        translator_nodedef.setNodeGroup("translation");
        translator_nodedef.setDocString(`Translator from '${source}' to '${target}'`);
        let version1 = source_nodedef.getVersionString();
        if (!version1) version1 = "1.0";
        translator_nodedef.setAttribute('source_version', version1);
        translator_nodedef.setAttribute('source', source);
        let version2 = target_nodedef.getVersionString();
        if (!version2) version2 = "1.0";
        translator_nodedef.setAttribute('target_version', version2);
        translator_nodedef.setAttribute('target', target);
        
        // Add inputs from source as inputs to the translator
        let comment = translator_nodedef.addChildOfCategory("comment");
        comment.setDocString(`Inputs (inputs from source '${source}')`);
        let inputs = source_nodedef.getActiveInputs();
        //console.log('>>>>>>>>>>>>>> ADD Inputs from source nodedef:', inputs.length);
        for (let input of inputs) {
            //console.log('-------------------------- Input:', input.getName(), input.getType());
            let nodedef_input = translator_nodedef.addInput(input.getName(), input.getType());
            if (input.hasValueString()) {
                nodedef_input.setValueString(input.getValueString(), input.getType());
            }
        }
        
        // Add inputs from target as outputs to the translator
        comment = translator_nodedef.addChildOfCategory("comment");
        comment.setDocString(`Outputs (inputs from target '${target}' with '_out' suffix)`);
        for (let input of target_nodedef.getActiveInputs()) {
            let output_name = input.getName() + "_out";
            translator_nodedef.addOutput(output_name, input.getType());
        }
        // 2. Create a new functional nodegraph
        comment = output_doc.addChildOfCategory("comment");
        comment.setDocString(`NodeGraph implementation for translator '${nodename}'`);
        let nodegraph_id = 'NG_' + nodename;
        let nodegraph = output_doc.addNodeGraph(nodegraph_id);
        nodegraph.setNodeDefString(derived_name);
        nodegraph.setDocString(`NodeGraph implementation of translator from '${source}' to '${target}'`);
        nodegraph.setAttribute('source_version', version1);
        nodegraph.setAttribute('source', source);
        nodegraph.setAttribute('target_version', version2);
        nodegraph.setAttribute('target', target);
        for (let output of translator_nodedef.getActiveOutputs()) {
            nodegraph.addOutput(output.getName(), output.getType());
        }
        if (mappings) {
            for (let [source_input_name, target_input_name] of Object.entries(mappings)) {
                let source_input = translator_nodedef.getInput(source_input_name);
                let output_name = target_input_name + "_out";
                let target_output = nodegraph.getOutput(output_name);
                if (source_input && target_output) {
                    let dot_name = nodegraph.createValidChildName(target_input_name);
                    let comment = nodegraph.addChildOfCategory("comment");
                    comment.setDocString(`Routing source input: '${source_input_name}' to target input: '${target_input_name}'`);
                    let dot_node = nodegraph.addNode('dot', dot_name);
                    let dot_input = dot_node.addInput('in', source_input.getType());
                    dot_input.setInterfaceName(source_input.getName());
                    target_output.setNodeName(dot_node.getName());
                }
            }
        }
        return translator_nodedef;
    }

    create_all_translators(definitions, output_doc = null) {
        /**
         * Create translators for all supported shading models.
         * @param {object} definitions - The source document containing Physically Based MaterialX definitions.
         * @param {object} output_doc - The document to add the translators to. If null, use the source doc.
         * @returns {object[]} A list of created translator definitions.
         */
        let trans_nodedefs = [];
        // Create temporary doc with all standard library definitions
        //let result = this.create_working_document();
        let trans_doc = this.mx.createDocument();
        let stdlib_defs = this.stdlib.getNodeDefs();
        console.log('> --------------------->>>>>>>>>> Use stdlib', stdlib_defs.length, 'definitions');
        trans_doc.setDataLibrary(this.stdlib);

        // Add Physically Based Material definitions to the temporary document
        trans_doc.copyContentFrom(definitions);
        this.add_copyright_docstring(output_doc, '');
        if (!output_doc) {
            console.log('No output document specified for translators');
            return trans_nodedefs;
        }
        // Source BSDF is always physbased_pbr_surface
        let source_bsdf = this.physlib_category;
        // Iterate over all target BSDFs
        let bsdfs = this.find_all_bxdf(trans_doc);
        for (let bsdf of bsdfs) {
            let bsdf_name = bsdf.getNodeString();
            if (bsdf_name === this.physlib_category) {
                continue;
            }
            let target_bsdf = bsdf.getNodeString();
            let remapping = this.getInputRemapping(target_bsdf);
            if (remapping && Object.keys(remapping).length > 0) {
                let trans_nodedef = this.create_translator(trans_doc, source_bsdf, target_bsdf, "", "", remapping, output_doc);
                if (trans_nodedef) {
                    console.log(`> Created translator to BSDF: ${bsdf_name}`);
                    trans_nodedefs.push(trans_nodedef);
                }
            }
        }
        return trans_nodedefs;
    }

    add_copyright_comment(doc, shaderCategory, embedDate = false) {

        // Add header comments
        this.addComment(doc, 'Physically Based Materials from https://api.physicallybased.info ');
        this.addComment(doc, '  Content Author: Anton Palmqvist, https://antonpalmqvist.com/ ');
        this.addComment(doc, `  Content processsed via REST API and mapped to MaterialX V${this.mx.getVersionString()} `);
        if (shaderCategory) {
            this.addComment(doc, `  Target Shading Model: ${shaderCategory} `);
        }
        this.addComment(doc, '  Utility Author: Bernard Kwok. kwokcb@gmail.com ');
        if (embedDate) {
            const now = new Date();
            const dt_string = now.getFullYear() + '-' + String(now.getMonth() + 1).padStart(2, '0') + '-' + String(now.getDate()).padStart(2, '0') + ' ' + String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0') + ':' + String(now.getSeconds()).padStart(2, '0');
            this.addComment(doc, `  Generated on: ${dt_string} `);
        }
    }

    create_definition(doc = null) {
        /**
         * Create a NodeDef for the Physically Based Material inputs
         * @param {object|null} doc - The MaterialX document to add the NodeDef to. If null, a new document will be created.
         * @returns {object} The MaterialX document with the created definition.
         */
        if (!doc) {
            doc = this.mx.createDocument();
            this.add_copyright_docstring(doc, '');
        }
        
        // Create placeholder nodegraph
        let graph = doc.addNodeGraph(this.get_physlib_implementation_name());
        graph.setNodeDefString(this.get_physlib_definition_name());
        let node = graph.addNode('oren_nayar_diffuse_bsdf', 'oren_nayar_diffuse_bsdf', 'BSDF');
        let node_in = node.addInput('color', 'color3');
        node_in.setInterfaceName('color');
        let node_in_rough = node.addInput('roughness', 'float');
        node_in_rough.setInterfaceName('roughness');
        node.addOutput('out', 'BSDF');
        node = graph.addNode('surface', 'surface', 'surfaceshader');
        node_in = node.addInput('bsdf', 'BSDF');
        node_in.setAttribute('out', 'out');
        node_in.setNodeName('oren_nayar_diffuse_bsdf');
        let node_out = graph.addOutput('out', 'surfaceshader');
        node_out.setNodeName('surface');
        
        // Create definition template
        let ndef = doc.addNodeDef(this.get_physlib_definition_name(), 'surfaceshader');
        ndef.setNodeString(this.physlib_category);
        ndef.setNodeGroup("pbr");
        ndef.setDocString("Node definitions for PhysicallyBased Material");
        ndef.setVersionString("1.0");
        ndef.setAttribute("isdefaultversion", "true");

        if (this.materials) {
            console.log('> Map keys to definition for materials:', this.materials.length);
            for (let mat of this.materials) {
                this.map_keys_to_definition(mat, ndef);
            }
        }
        else {
            console.log('>  No materials to map keys to definition');
        }
        return doc;
    }

    create_definition_materials(doc_mat, filter_list = null) {
        /**
         * Create a MaterialX document containing Physically Based MaterialX materials
         * @param {object|null} doc_mat - The MaterialX document to add the materials to
         * @param {string[]|null} filter_list - A list of material names to filter. If null, all materials will be processed.
         * @returns {object} The MaterialX document containing the materials
         */
        let definitions = this.get_definitions();
        if (!doc_mat) {
            doc_mat = this.mx.createDocument();
            this.add_copyright_docstring(doc_mat, '');
        }
        // Reference the library definitions into the material document
        doc_mat.setDataLibrary(definitions);
        for (let mat of this.materials) {

            let matName = mat['name'];
            if (filter_list && !filter_list.includes(matName)) {
                continue;
            }

            let shaderName = doc_mat.createValidChildName(matName + '_SHD_PBM');
            //console.log('************* Create material for:', mat['name'], '-> shader name:', shaderName, filter_list);

            let shaderNode = doc_mat.addNode(this.physlib_category, shaderName, this.mx.SURFACE_SHADER_TYPE_STRING);
            for (let [key, value] of Object.entries(mat)) {
                if (!value){
                    continue;
                }

                if (key === 'name') {
                    let new_name = doc_mat.createValidChildName(String(value));
                    shaderNode.setName(new_name);
                }
                let input = shaderNode.addInputFromNodeDef(key);
                if (input) {
                    //console.log('> Add input for key:', key, 'value:', value, 'input:', input.getName());
                    if (Array.isArray(value)) {
                        value = value.map(x => String(x)).join(', ');
                    }
                    input.setValueString(String(value), input.getType());
                    // Add doc string
                    let doc_string = '';
                    if (key === 'description') {
                        doc_string = String(value);
                    }
                    if (doc_string.length > 0) {
                        shaderNode.setDocString(doc_string);
                    }
                }
            }
            shaderNode.setAttribute('uiname', matName);

            // Create a new material
            let materialName = doc_mat.createValidChildName(matName + '_MAT_PBM');
            let materialNode = doc_mat.addNode(this.mx.SURFACE_MATERIAL_NODE_STRING, materialName, this.mx.MATERIAL_TYPE_STRING);
            let shaderInput = materialNode.addInput(this.mx.SURFACE_SHADER_TYPE_STRING, this.mx.SURFACE_SHADER_TYPE_STRING);
            shaderInput.setAttribute(MTLX_NODE_NAME_ATTRIBUTE, shaderNode.getName());
        }
        return doc_mat;
    }

    find_translator(doc, source, target) {
        /**
         * Find a translator nodedef from source to target in the document.
         * @param {object} doc - The MaterialX document to search.
         * @param {string} source - The source definition category.
         * @param {string} target - The target definition category.
         * @returns {object|null} The translator nodedef if found, otherwise null.
         */
        let derived_name = this.derive_translator_name_from_targets(source, target);
        let translator_nodedef = doc.getNodeDef(derived_name);
        return translator_nodedef;
    }

    translate_node(doc, source_bxdf, target_bxdf, node) {
        /**
         * Translate a shader node of source_bxdf to target_bxdf using ungrouped nodes.
         * This function creates a target node and a translation node based on the translator nodedef, then makes upstream and downstream connections.
         * @param {object} doc - The document to operate on.
         * @param {string} source_bxdf - The source BXDF shading model name.
         * @param {string} target_bxdf - The target BXDF shading model name.
         * @param {object} node - The source shader node to translate.
         * @returns {object|null} An object with 'translationNode' and 'targetNode' if successful, null otherwise.
         */
        let nodedef = this.find_translator(doc, source_bxdf, target_bxdf);
        if (!nodedef) {
            console.warn(`- No translator found from '${source_bxdf}' to '${target_bxdf}' for node '${node.getName()}'`);
            return null;
        }
        // Create a target node of the target_bxdf category.
        let replace_name = node.getName();
        let target_node_name = doc.createValidChildName(`${replace_name}_${target_bxdf}_SPB`); 

        // Cleanup dowstream connections
        let downstream_ports = node.getDownstreamPorts()
        for (let port of downstream_ports) {
            //console.log('Scan downstream port:', port.getName(), 'of node:', port.getParent().getName());
            let downstream_node = port.getParent();
            let downstream_input = downstream_node.getInput(port.getName());
            if (downstream_input) {
                //console.log(` - Reconnecting downstream node '${downstream_node.getName()}' input '${downstream_input.getName()}' from '${node.getName()}' to target node '${target_node_name}'`);
                downstream_input.setNodeName(target_node_name);
            }
        }

        let targetNode = doc.addChildOfCategory(target_bxdf, target_node_name);
        if (!targetNode) {
            console.warn(`- Failed to create target node of category '${target_bxdf}' for node '${node.getName()}'`);
            return null;
        }
        targetNode.setType("surfaceshader");
        // WARNING: addInputsFromNodeDef() is missing from MaterialX JS API as of 1.39.5 !
        //targetNode.addInputsFromNodeDef();
        //const targetNodeDef = targetNode.getNodeDef();
        //for (let input of targetNodeDef.getActiveInputs()) {
        //    let targetInput = targetNode.addInputFromNodeDef(input.getName());
        //}

        // Create a translation node based on the translator nodedef.
        let translationNode = doc.addNodeInstance(nodedef, 
                            targetNode.getName() + "_translator");

        // Copy over inputs from the source node to the translation node.
        let num_overrides = 0;
        for (let input of node.getActiveInputs()) {
            let translationInput = translationNode.addInputFromNodeDef(input.getName());
            if (translationInput) {
                translationInput.copyContentFrom(input);
                num_overrides += 1;
            }
        }

        // Connect translation outputs to target inputs.
        const impl = nodedef.getImplementation();
        for (let output of nodedef.getActiveOutputs()) {

            // Avoid adding ports which do not route an input data
            const impl_output = impl.getOutput(output.getName());
            if (!impl_output.getConnectedNode()) {
                continue;
            }

            let target_input_name = output.getName();
            // Remove trailing '_out' from name
            if (target_input_name.endsWith('_out')) {
                target_input_name = target_input_name.slice(0, -4);
            }

            let translationOutput = translationNode.addOutput(output.getName(), output.getType());
            translationOutput.copyContentFrom(output);

            let target_input = targetNode.addInputFromNodeDef(target_input_name);
            if (!target_input) {
                console.info(` - Warning: Target node '${targetNode.getName()}' has no input named '${target_input_name}' for output '${output.getName()}'`);
                continue;
            } else {
                target_input.setNodeName(translationNode.getName());
                target_input.setOutputString(translationOutput.getName());
                target_input.removeAttribute('value');
            }
        }
     

        // Remove original node
        doc.removeNode(replace_name);

        return { 'translationNode': translationNode, 'targetNode': targetNode };
    }

    
    initialize_definitions_and_materials(shadingModel = 'standard_surface', materialNames = [], force=false) {
        /**
         * @brief Initialize Physically Based MaterialX definitions, materials, remappings, and translators.
         * @returns {void}
         */

        console.log('> Generate for shading model:', shadingModel, 'materials filer:', materialNames);
        
        if (!this.physlib || force) {

            // Create Physically Based MaterialX definition library
            this.physlib = this.create_definition(null);
            console.log('> Created Physically Based MaterialX definition library...');
        }

        let translated_doc = null;
        let untranslated_doc = null;
        if (!this.physlib_materials || !this.physlib_translators || force) {
            // Create all translators
            this.physlib_translators = this.mx.createDocument();
            this.create_all_translators(this.physlib, this.physlib_translators);

            // Create Physically Based MaterialX materials library
            let filter_list = null;
            this.physlib_materials = this.create_definition_materials(null, filter_list);
        }

        untranslated_doc = this.physlib_materials;
 
        if (materialNames.length > 0) {

            // Translate specified materials
            //
            untranslated_doc = this.create_definition_materials(null, materialNames);
            translated_doc = this.mx.createDocument();
            translated_doc.copyContentFrom(untranslated_doc);
            translated_doc.setDataLibrary(this.get_definitions());
            const category = this.get_physlib_category()
            for (const node of translated_doc.getNodes()) {
                if (materialNames.length > 0 && !materialNames.includes(node.getName())) {
                    continue;
                }
                if (node.getCategory() == 'physbased_pbr_surface')
                {
                    console.log('> Translate specified material:', node.getName());
                    let result = this.translate_node(translated_doc, 'physbased_pbr_surface', shadingModel, node)
                }
            }

        }
        else 
        {
            // Translate all material
            //
            if (!(shadingModel in this.translated_materials) || force) {        

                const category = this.get_physlib_category()
                console.log('> Translating all materials from', category, 'to', shadingModel);

                // Create translated materials for specified shader model
                translated_doc = this.mx.createDocument();
                translated_doc.copyContentFrom(this.physlib_materials);
                translated_doc.setDataLibrary(this.get_definitions());
                for (const node of translated_doc.getNodes()) {
                    if (node.getCategory() == 'physbased_pbr_surface')
                    {
                        let result = this.translate_node(translated_doc, 'physbased_pbr_surface', shadingModel, node)
                    }
                }
                this.translated_materials[shadingModel] = translated_doc;
            }
            else {
                translated_doc = this.translated_materials[shadingModel];
            }
        }

        let def_string = this.mx.writeToXmlString(this.physlib);
        //console.log('> Physically Based MaterialX Definition Library:\n', def_string);
        let trans_string = this.mx.writeToXmlString(this.physlib_translators);
        //console.log('> Physically Based MaterialX Translators Library:\n', trans_string);   
        let mat_string = this.mx.writeToXmlString(untranslated_doc);
        //console.log('> Physically Based MaterialX Materials Library:\n', mat_string);        
        let mat_trans_string = this.mx.writeToXmlString(translated_doc);
        
        return { 'bsdf': def_string, 
            'bsdf_trans': trans_string, 
            'bsdf_materials': mat_string,
            'bsdf_trans_materials': mat_trans_string };
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
                    console.log('- No remap keys from repo. Using default remap keys.');
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
            // Re-initialize cached information
            this.materials = null
            this.materialNames = [];
            this.physlib = null;
            this.physlib_materials = null;
            this.physlib_translators = null;
            this.translated_materials = {};

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

                this.esslgenerator = new this.mx.EsslShaderGenerator.create();
                this.esslgenContext = new this.mx.GenContext(this.esslgenerator);
                this.stdlib = this.mx.loadStandardLibraries(this.esslgenContext);
                let children = this.stdlib.getChildren();
                for (let i = 0; i < children.length; i++) {
                    let child = children[i];
                    child.setSourceUri('STDLIB_ELEMENT');
                }

                let nodedefs = this.stdlib.getNodeDefs();                
                console.log("MaterialX is loaded. With ", nodedefs.length, "definitions.");
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
     * Return a sorted list reference names mapped reference images.
     * @returns {object[]} - List of references. 
     */
    getReferenceList()
    {
        let references = [];
        if (this.materials) {
            for (let i = 0; i < this.materials.length; i++) {
                const mat = this.materials[i];
                const matName = mat['name'];
                const refString = mat['reference']; 
                const tags = mat['tags'];
                const category = mat['category'];
                if (refString.length > 0)
                {
                    let referenceItem = { name: matName, reference: refString[0], tags: tags, category: category };
                    //console.log('Add Reference:', referenceItem);
                    references.push(referenceItem);
                }
            }
            // Sort references by name
            references.sort((a, b) => a.name.localeCompare(b.name));
        }
        return references;
    }

    /**
     * @brief Add copyright docstring to the MaterialX document
     * @param doc MaterialX document
     * @param shaderCategory - MaterialX shader category (optional) 
     */
    add_copyright_docstring(doc, shaderCategory = '') 
    {
        // Add document level accreditation
        let docString = 'Physically Based Materials from https://api.physicallybased.info.\n'
        docString += '  Content Author: Anton Palmqvist, https://antonpalmqvist.com/ \n'
        docString += `  Content processsed via REST API and mapped to MaterialX V${this.mx.getVersionString()} \n`
        if (shaderCategory.length > 0) {
            docString +=  `  Target Shading Model: ${shaderCategory} \n`
        }
        docString +=  '  Utility Author: Bernard Kwok. kwokcb@gmail.com '  
        doc.setDocString(docString);
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

        if (Object.keys(remapKeys).length === 0)
        {
            remapKeys = this.getInputRemapping(shaderCategory);
        }
        //console.log('Using remap keys for shading model:', shaderCategory, remapKeys);

        // Create a dummy doc with the surface shader with all inputs
        // as reference
        let refDoc = this.mx.createDocument();
        refDoc.importLibrary(this.stdlib);
        const refNode = refDoc.addNode(shaderCategory, 'refShader', this.mx.SURFACE_SHADER_TYPE_STRING);
        if (addAllInputs) {
            console.warn('MaterialX JS API missing addInputsFromNodeDef()');
            //refNode.addInputsFromNodeDef() -- This is missing from the JS API.
        }
        this.doc = this.mx.createDocument();

        // Add document level accreditation
        this.add_copyright_docstring(this.doc, shaderCategory);

        // Add properties to the material
        for (let i = 0; i < this.materials.length; i++) {
            const mat = this.materials[i];
            let matName = mat['name'];

            // Filter by material name(s)
            let skipGeneration = materialNames.length > 0 && !materialNames.includes(matName);

            let shaderNode = null;
            let docString = ''
            if (!skipGeneration) 
            {
                if (shaderPreFix.length > 0) {
                    matName = shaderPreFix + '_' + matName;
                }

                const shaderName = this.doc.createValidChildName(matName + '_' + shaderCategory + '_SPB');
                this.addComment(this.doc, ' Generated shader: ' + matName + ' ');
                shaderNode = this.doc.addNode(shaderCategory, shaderName, this.mx.SURFACE_SHADER_TYPE_STRING);

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

                if (mat['description'].length > 0) {
                    docString += 'Description: ' + mat['description'];
                }
            }

            // Always want to build the reference
            const refString = mat['reference'];
            if (refString.length > 0) {
                if (docString.length > 0) {
                    docString += '. ';
                }
                docString += 'Reference: ' + refString[0];

                let referenceItem = { name: matName, reference: refString[0] };
                //console.log('Add Reference:', referenceItem);
                references.push(referenceItem);
            }
            // Sort references by name
            references.sort((a, b) => a.name.localeCompare(b.name));

            if (!shaderNode) {
                continue;
            }
            if (docString.length > 0) {
                shaderNode.setDocString(docString);
            }

            // Create a new material
            const materialName = this.doc.createValidChildName(matName + '_' + shaderCategory + '_MPB');
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

                    //console.log(`-- Processing key: "${key}" with value:`, value);

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

                    //console.log(`-- Remapping key "${key}" to "${remapKeys[key]}"`);
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
                        //console.log('>> Could not map input:', key, 'to node definition')
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
