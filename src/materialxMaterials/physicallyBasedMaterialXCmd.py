#/usr/bin/env python3
'''
@brief Command to convert Physically Based Materials to MaterialX Command Line Utility
@details This script converts Physically Based Materials to MaterialX using the MaterialX Python API.
@details The script can be run from the command line with the following options:
@details --shadingModel: Shading models to use for conversion. If not specified then all will be used.
@details Options: standard_surface, gltf_pbr, open_pbr_surface
@details --outputDir: Output directory for MaterialX files
@details --writeJSON: Write materials JSON file. Default is True
@details --separateFiles: Convert individual MaterialX files per material. Default is false
@details Example usage:
@details - python physicallyBasedMaterialXCmd.py
@details - python physicallyBasedMaterialXCmd.py --outputDir=myfolder
@details - python physicallyBasedMaterialXCmd.py --writeJSON=False 
@details - python physicallyBasedMaterialXCmd.py --shadingModel=gltf_pbr,open_pbr_surface
@details - python physicallyBasedMaterialXCmd.py --shadingModel=open_pbr_surface --separateFiles=True
'''
from pydoc import doc
from unittest import loader
import os, sys, argparse, logging
from venv import logger

import MaterialX as mx # type: ignore
import physicallyBasedMaterialX as pbmx

def physicallBasedMaterialXCmd():
    '''
    Command to parse PhysicallyBased materials and create MaterialX materials
    '''
    logger = logging.getLogger('PB_CMD')
    logging.basicConfig(level=logging.INFO)

    # TODO: Add arguments for shading model, and output directory using argparse
    parser = argparse.ArgumentParser(description='Convert Physically Based Materials to MaterialX')
    parser.add_argument('-m', '--shadingModel', type=str, default='', help='Shading models to use for conversion. '
                        ' If not specified then all will be used. '
                        ' Options: standard_surface, gltf_pbr, open_pbr_surface')
    parser.add_argument('-o', '--outputDir', type=str, default='', 
                        help='Output directory for MaterialX files. Default location is PhysicallyBasedMaterialX')
    parser.add_argument('-j', '--writeJSON', type=bool, default=True, 
                        help='Write materials JSON file. Default is True')
    parser.add_argument('-s', '--separateFiles', type=bool, default=False, 
                        help='Convert individual MaterialX files per material. Default is false')
    parser.add_argument('-l', '--loadFromFile', type=str, default='', help='Load materials a specified file')
    parser.add_argument('-wr', '--writeRemapping', type=bool, default=False, help='Write remapping from PhysicallyBased to MaterialX. Default is False')
    parser.add_argument('-rr', '--readRemapping', type=str, default='', help='Read remapping from PhysicallyBased to MaterialX. Default is empty')
    parser.add_argument('-nd', '--createNodeDef', type=bool, default=False, help='Create NodeDef for Physically Based Material inputs. Default is False')
    opts = parser.parse_args()

    outputDir = 'PhysicallyBasedMaterialX'
    if opts.outputDir:
        if not os.path.exists(opts.outputDir):
            logger.info(f'Error: Output directory does not exist: {opts.outputDir}')
            # Create the output directory
            try:
                os.makedirs(opts.outputDir)
                logger.info(f'> Created output directory: {opts.outputDir}')
                outputDir = opts.outputDir
            except Exception as e:
                logger.info(f'> Error: Could not create output directory: {opts.outputDir}')
                sys.exit(1)
        else:
            outputDir = opts.outputDir

    shadingModels = []
    if opts.shadingModel:
        shadingModels = opts.shadingModel.split(',')        
    shadingModePrefixMap = { 'standard_surface': 'SS', 'gltf_pbr': 'GLTF', 'open_pbr_surface': 'OPBR' }
    shadingModelPrefixes = []
    if len(shadingModels) == 0:
        shadingModels = ['standard_surface', 'gltf_pbr', 'open_pbr_surface']
        shadingModelPrefixes = ['SS', 'GLTF', 'OPBR']
    else:
        for shadingModel in shadingModels:
            shadingModelPrefixes.append(shadingModePrefixMap[shadingModel])

    writeJSON = opts.writeJSON
    separateFiles = opts.separateFiles

    # Create loader and get PhysicallyBasedMaterials
    jsonMat = None
    loader = pbmx.PhysicallyBasedMaterialLoader(mx, None)

    readRemapping = opts.readRemapping
    if readRemapping:
        if not os.path.exists(readRemapping):
            logger.info(f'> Error: Remapping file does not exist: {readRemapping}')
        logger.info(f'> Read remapping file: {readRemapping}')
        loader.readRemappingFile(readRemapping)
    else:
        writeRemapping = opts.writeRemapping
        if writeRemapping:
            outputFile = os.path.join(outputDir, 'PhysicallyBasedToMtlxMappings.json')
            logger.info(f'> Write remapping file: {outputFile}')
            loader.writeRemappingFile(outputFile)

    if opts.loadFromFile:
        if not os.path.exists(opts.loadFromFile):
            logger.info(f'> Error: File does not exist: {opts.loadFromFile}')
            sys.exit(1)
        logger.info(f'> Load materials from file: {opts.loadFromFile}')
        jsonMat = loader.loadMaterialsFromFile(opts.loadFromFile)
    else:
        jsonMat = loader.getMaterialsFromURL()

    if jsonMat:

        # Create folder for MaterialX call PhysicallyBasedMaterialX
        os.makedirs(outputDir, exist_ok=True)

        create_nodedef = opts.createNodeDef
        if create_nodedef:

            # Create PhysicallyBased BSDF definition
            #
            logger.info('> Create definition for PhysicallyBased materials')
            doc = None
            doc, definition = loader.create_definition(doc)
            if doc:
                status, error = doc.validate()
                if not status:
                    logger.error('> Error validating NodeDef document:')
                    logger.error(error)
                else:
                    logger.info('> Definition documents passed validation.')

                nodedef_file_name = os.path.join(outputDir, 'physbased_pbr.mtlx')
                mx.writeToXmlFile(doc, nodedef_file_name)
                logger.info(f'> Write definition file: {nodedef_file_name}')

            # Create PhysicallyBased materials using the definition
            #
            doc_mat = None
            filter_list = []
            doc_mat = loader.create_definition_materials(doc_mat, doc, filter_list)

            if doc_mat:
                status, error = doc_mat.validate()
                if not status:
                    logger.error('> Error validating definition materials document:')
                    logger.error(error)
                else:
                    logger.info('> Definition materials document passed validation.')

                nodedef_mat_file_name = os.path.join(outputDir, 'physbased_pbr_materials.mtlx')
                mx.writeToXmlFile(doc_mat, mx.FilePath(nodedef_mat_file_name))
                logger.info(f'> Write materials file: {nodedef_mat_file_name}')

            # Create translator definitions
            #
            translations_doc = mx.createDocument()
            resulting_definitions = loader.create_all_translators(doc, translations_doc)
            print(f'Number of translator definitions created: {len(resulting_definitions)}')

            if resulting_definitions and translations_doc:     
                output_file_name = 'physbased_pbr_translators.mtlx'
                output_path = os.path.join(outputDir, output_file_name)                
                logger.info('> Write translator file:' + output_path)
                mx.writeToXmlFile(translations_doc, mx.FilePath(output_path))

            # Doc with stdlib
            result = loader.create_working_document()
            stdlib = result['stdlib']
            # Add Physically Based Material definitions 
            stdlib.copyContentFrom(doc)
            stdlib.copyContentFrom(translations_doc)
            
            if not separateFiles:
                translated_doc = mx.createDocument()
                translated_doc.setDataLibrary(stdlib)

                # Copy over materials
                translated_doc.copyContentFrom(doc_mat)

                for shadingModel, prefix in zip(shadingModels, shadingModelPrefixes):

                    for node in translated_doc.getNodes():
                        if node.getCategory() == 'physbased_pbr_surface':
                            trans_result = loader.translate_node(translated_doc, 'physbased_pbr_surface', shadingModel, node)

                    logger.info(f'> Generate MaterialX using nodedefs for shading model: {shadingModel}')
                    fileName = os.path.join(outputDir, f'PhysicallyBasedMaterialX_translated_{prefix}.mtlx')
                    loader.writeMaterialXToFile(fileName, translated_doc)
                    logger.info(f'> Write: {fileName}')
        
            else:
                matDir = os.path.join(outputDir, 'Sep')
                os.makedirs(matDir, exist_ok=True)
                for shadingModel, prefix in zip(shadingModels, shadingModelPrefixes):
                    converted = []
                    for mat in loader.getJSONMaterialNames():
                        materialFilter = [mat]
                        
                        # Create doc with single material
                        matdoc = loader.create_definition_materials(None, doc, materialFilter)
                        if matdoc is not None:
                            # Set up definitions
                            matdoc.setDataLibrary(stdlib)
    
                            # Translate the material
                            mat_name = mx.createValidName(mat)  
                            node = matdoc.getNode(mat_name)
                            if node:
                                trans_result = loader.translate_node(matdoc, 'physbased_pbr_surface', shadingModel, node)
                                if not trans_result:
                                    logger.warning(f'Failed to translate node: {mat_name} for shading model: {shadingModel}')
                                else:
                                    converted.append(trans_result['targetNode'].getName())
                                    valid, errors = loader.validateMaterialXDocument(matdoc)
                                    if valid:
                                        #logger.info(f'> Generate material {mat_name} for shading model: {shadingModel}')
                                        fileName = os.path.join(matDir, f'PB_{prefix}_{mat}.mtlx')
                                        loader.writeMaterialXToFile(fileName, matdoc)
                                        
                    logger.info(f'> Converted {len(converted)} materials for shading model: {shadingModel}')

        if writeJSON:
            logger.info(f'> Write PB material file: {outputDir}/PhysicallyBasedMaterial.json')
            loader.writeJSONToFile(os.path.join(outputDir, 'PhysicallyBasedMaterial.json'))

        if create_nodedef:
            return

        # Direct translation from JSON to MaterialX path. Skip if using PhysicallyBased nodedefs
        if not separateFiles:
            for shadingModel, prefix in zip(shadingModels, shadingModelPrefixes):
                logger.info(f'> Generate MaterialX for shading model: {shadingModel}')
                matdoc = loader.convertToMaterialX([], shadingModel, {}, prefix)
                valid, errors = loader.validateMaterialXDocument(matdoc)
                if valid:
                    fileName = os.path.join(outputDir, f'PhysicallyBasedMaterialX_{prefix}.mtlx')
                    loader.writeMaterialXToFile(fileName)
                    logger.info(f'> Write: {fileName}')
    
        else:
            for shadingModel, prefix in zip(shadingModels, shadingModelPrefixes):
                logger.info(f'> Generate MaterialX for shading model: {shadingModel}')
                for mat in loader.getJSONMaterialNames():
                    materialFilter = [mat]
                    matdoc = loader.convertToMaterialX(materialFilter, shadingModel, {}, prefix)
                    if matdoc is not None:
                        valid, errors = loader.validateMaterialXDocument(matdoc)
                        if valid:
                            fileName = os.path.join(outputDir, f'PB_{prefix}_{mat}.mtlx')
                            loader.writeMaterialXToFile(fileName)
                            logger.info(f'> Write: {fileName}')

    else:
        logger.info('Could not retrieve PhysicallyBased Materials')

if __name__ == '__main__':
    physicallBasedMaterialXCmd()