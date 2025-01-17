#/usr/bin/env python3

import os, argparse, sys, logging
import ambientCGLoader as acg
import MaterialX as mx

def ambientCgLoaderCmd():
    '''
    Utility to download and write ambientCG materials
    '''
    logger = logging.getLogger('ACG_CMD')
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description='Get materials information and material package from ambientCG.'
                                     ' By default the materials will be downloaded and a named and index material'
                                     ' package will be extracted.')

    parser.add_argument('--loadMaterials', type=str, default='', 
                        help='File containing list of materials and download information')
    # TODO: Add a --downloadMaterials

    parser.add_argument('--materialNames', type=bool, default=None,
                        help='Return material names. Default is False')
    
    parser.add_argument('--saveMaterials', type=bool, default=None, 
                        help='Save material lists. Default is None.'
                        ' Has no effect if --loadMaterials is set')    
    parser.add_argument('--saveMaterial', type=str, default='', 
                        help='Save material download information in JSON format')

    # Asset download options
    parser.add_argument('--downloadMaterial', type=str, default='', 
                        help='Download zip package for a materials which match a given string. Default is a sample material')
    parser.add_argument('--downloadmageFormat', type=str, default='PNG', 
                        help='Download image format. Valid values include PNG and JPEG. Default is PNG')
    parser.add_argument('--downloadResolution', type=str, default='1', 
                        help='Download image resulution. Valid values include 1,2,4,8 to indicate 1K to 8K.')

    parser.add_argument('--output', type=str, default='', 
                        help='Output folder for data files. Default location is the current execution folder.')
    opts = parser.parse_args()

    loader = acg.AmbientCGLoader(mx, None)
    
    outputFolder = '.'
    if opts.output:
        outputFolder = opts.output
    if not os.path.exists(outputFolder):
        logger.error(f'Error: Output directory does not exist: {outputFolder}')
        sys.exit(1)
    
    getMaterials = False
    materialName = opts.downloadMaterial
    downloadMaterial = len(materialName) > 0
    if opts.materialNames or downloadMaterial or opts.saveMaterials:
        getMaterials = True

    loadMaterials = opts.loadMaterials
    materialsList = None
    if len(loadMaterials) > 0:
        materialsList = loader.loadMaterialsList(loadMaterials)
    elif getMaterials:
        materialsList = loader.downloadMaterialsList()
        loader.writeMaterialList(materialsList, os.path.join(outputFolder,'ambientCG_materialsList.json'))

    if opts.materialNames:
        materialNames = loader.getMaterialNames()
        print(f'Found: {len(materialNames)} materials, {materialNames}')        

    if downloadMaterial:
        result = loader.findMaterial(materialName)
        if result:
            loader.downloadMaterial(materialName, outputFolder, opts.downloadmageFormat, opts.downloadResolution)
        else:
            print(f'Material not found: {materialName}')                

if __name__ == '__main__':
    ambientCgLoaderCmd()