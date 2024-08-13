#/usr/bin/env python3
'''
@file physicallyBasedMaterialXCmd.py
@brief Convert Physically Based Materials to MaterialX Command Line Utility
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
import os, sys, argparse, logging

import MaterialX as mx
import physicallyBasedMaterialX as pbmx

def main():
    logger = logging.getLogger('PBCMD')
    logging.basicConfig(level=logging.INFO)

    # Add arguments for shading model, and output directory using argparse
    parser = argparse.ArgumentParser(description='Convert Physically Based Materials to MaterialX')
    parser.add_argument('--shadingModel', type=str, default='', help='Shading models to use for conversion. '
                        ' If not specified then all will be used. '
                        ' Options: standard_surface, gltf_pbr, open_pbr_surface')
    parser.add_argument('--outputDir', type=str, default='PhysicallyBasedMaterialX', 
                        help='Output directory for MaterialX files')
    parser.add_argument('--writeJSON', type=bool, default=True, 
                        help='Write materials JSON file. Default is True')
    parser.add_argument('--separateFiles', type=bool, default=False, 
                        help='Convert individual MaterialX files per material. Default is false')
    parser.add_argument('--loadFromFile', type=str, default='', help='Load materials a specified file')
    opts = parser.parse_args()

    outputDir = 'PhysicallyBasedMaterialX'
    if opts.outputDir:
        if not os.path.exists(opts.outputDir):
            logger.info(f'Error: Output directory does not exist: {opts.outputDir}')
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

        if writeJSON:
            logger.info(f'> Write: {outputDir}/PhysicallyBasedMaterial.json')
            loader.writeJSONToFile(os.path.join(outputDir, 'PhysicallyBasedMaterial.json'))

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
                    valid, errors = loader.validateMaterialXDocument(matdoc)
                    if valid:
                        fileName = os.path.join(outputDir, f'PB_{prefix}_{mat}.mtlx')
                        loader.writeMaterialXToFile(fileName)
                        logger.info(f'> Write: {fileName}')

    else:
        logger.info('Could not retrieve PhysicallyBased Materials')

if __name__ == '__main__':
    main()