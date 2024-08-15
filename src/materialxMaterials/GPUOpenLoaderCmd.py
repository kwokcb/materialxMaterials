#/usr/bin/env python3

import os, argparse, sys, logging
import GPUOpenLoader as gpuo

def GPUOpenLoaderCmd():
    '''
    Utility to download and write GPUOpen materials
    '''
    logger = logging.getLogger('GPUO_CMD')
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description='Get materials information and material package from AMD GPUOpen.'
                                     ' By default the materials will be downloaded and a named and index material'
                                     ' package will be extracted.')
    parser.add_argument('--materialNames', type=bool, default=None,
                        help='Return material names. Default is False')
    #parser.add_argument('--loadMaterials', type=str, default='', 
    #                    help='Folder to load materials from. All JSON files with post-fix _#.json are loaded. Default is false'
    #                    ' meaning to download materials')
    parser.add_argument('--saveMaterials', type=bool, default=None, 
                        help='Save material lists. Default is None.'
                        ' Has no effect if --loadMaterials is set')
    parser.add_argument('--extractExpression', type=str, default='Oliana Blue Painted Wood', 
                        help='Extract out a package for a materials which match a given expression. Default is a sample material'
                        ' Has no effect if --loadMaterials is set')
    parser.add_argument('--extractIndices', type=str, default='0,1,0', 
                        help='Extract out a package for a materials which match a given material list, material index, and package index.'
                        ' Default is 0,1,0 which is currently the "Emerald Peaks Wallpaper" material')
    parser.add_argument('--output', type=str, default='', 
                        help='Output folder for data files. Default location is GPUOpenMaterialX.'
                        ' Has no effect if --loadMaterials is set')
    opts = parser.parse_args()

    loader = gpuo.GPUOpenMaterialLoader()

    # TODO: Add support for this
    #if opts.loadMaterials:
    #    logger.info(f'> Load materials from folder: {opts.loadMaterials}')  
    #    return
    
    outputFolder = 'GPUOpenMaterialX'
    if opts.output:
        if not os.path.exists(opts.output):
            logger.error(f'Error: Output directory does not exist: {opts.output}')
            sys.exit(1)
        else:
            outputFolder = opts.output

    # Download materials
    materials = loader.getMaterials()
    materialNames = loader.getMaterialNames()
    materialCount = len(materialNames)
    logger.info(f'Available number of materials: {materialCount}')
    if opts.saveMaterials:
        loader.writeMaterialFiles(outputFolder, 'GPUOpenMaterialX')

    # Create a test expression
    searchExpr = ''
    if opts.extractExpression:
        searchExpr = opts.extractExpression
    if len(searchExpr) == 0:
        logger.info(f'> No search expression given.')
    else:    
        dataItems = loader.downloadPackageByExpression(searchExpr, 0)
        for dataItem in dataItems:
            data = dataItem[0]
            title = dataItem[1]
            loader.writePackageDataToFile(data, outputFolder, title)    

    extractIndices = opts.extractIndices
    if len(extractIndices) > 0:
        indices = extractIndices.split(',')
        if len(indices) != 3:
            logger.error(f'Error: Invalid indices given: {extractIndices}')
            sys.exit(1)

        materialList = int(indices[0])
        materialIndex = int(indices[1])
        materialPackage = int(indices[2])
        [data, title] = loader.downloadPackage(materialList, materialIndex, materialPackage)
        logger.info(f'> Download material: {title} List: {materialList}. Index: {materialIndex}. Package: {materialPackage}')
        if data:
            loader.writePackageDataToFile(data, outputFolder, title)    

    if opts.materialNames:
        materialNamesFile = os.path.join(outputFolder, 'GPUOpenMaterialX_Names.json')
        logger.info(f'> Save materials names to file: {materialNamesFile}')
        sorted = True
        loader.writeMaterialNamesToFile(materialNamesFile, sorted)

if __name__ == '__main__':
    GPUOpenLoaderCmd()