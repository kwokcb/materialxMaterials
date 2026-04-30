#/usr/bin/env python3
'''
@brief Command to download GPUOpen MaterialX materials
'''
import os, argparse, sys, logging
import GPUOpenLoader as gpuo

def GPUOpenLoaderCmd():
    '''
    @brief Command to download GPUOpen materials
    '''
    logger = logging.getLogger('GPUO_CMD')
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description='Get materials information and material package from AMD GPUOpen.'
                                     ' By default the materials will be downloaded and a named and index material'
                                     ' package will be extracted.')
    parser.add_argument('--materialNames', type=bool, default=None,
                        help='Return material names. Default is False')
    parser.add_argument('--loadFromPackage', type=bool, default=None,
                        help='Load materials from a package. Default is True. If false, materials will be downloaded.')
    parser.add_argument('--loadMaterials', type=str, default='', 
                        help='Folder to load materials from. All JSON files with post-fix _#.json are loaded. Default is false'
                        ' meaning to download materials')
    parser.add_argument('--saveMaterials', type=bool, default=None, 
                        help='Save material lists. Default is None.'
                        ' Has no effect if --loadMaterials is set')
    parser.add_argument('--extractExpression', type=str, default='', 
                        help='Extract out a package for a materials which match a given expression. Default is a sample material'
                        )
    parser.add_argument('--extractIndices', type=str, default='', 
                        help='Extract out a package for a materials which match a given material list, material index, and package index.'
                        ' Default is empty. Format is: <materialList>,<materialIndex>,<materialPackage>')
    parser.add_argument('--output', type=str, default='', 
                        help='Output folder for data files. Default location is GPUOpenMaterialX.')
    parser.add_argument('--unzip', type=bool, default=None, 
                        help='Unzip the downloaded package. Default is None.')
    opts = parser.parse_args()

    loader = gpuo.GPUOpenMaterialLoader()
    materials = None

    if opts.loadFromPackage:
        logger.info(f'> Load materials from package')
        materials = loader.readPackageFiles()
    else:
        if opts.loadMaterials:
            filePaths = loader.getMaterialFileNames(opts.loadMaterials)
            if len(filePaths) == 0:
                logger.error(f'Error: No files found in folder: {opts.loadMaterials}')
                sys.exit(1)

            logger.info(f'> Load materials from files: {filePaths}')
            materials = loader.readMaterialFiles(filePaths)
        else:
            # Download materials
            logger.info(f'> Download materials from GPUOpen')
            materials = loader.getMaterials()
            # Download renders
            renders = loader.getRenders(force=True)
            loader.getMaterialPreviews()
    
    outputFolder = 'GPUOpenMaterialX'
    if opts.output:
        if not os.path.exists(opts.output):
            logger.error(f'Error: Output directory does not exist: {opts.output}')
            sys.exit(1)
        else:
            outputFolder = opts.output

    materialNames = loader.getMaterialNames()
    materialCount = len(materialNames)
    previewCount = len(loader.getMaterialPreviews())
    rendersCount = len(loader.getRenders(force=False)['renders'])
    logger.info(f'Have {materialCount} materials and {previewCount} previews, and {rendersCount} renders.')
    if opts.saveMaterials:
        loader.writeMaterialFiles(outputFolder, 'GPUOpenMaterialX')
        loader.writeRenderFiles(outputFolder, 'GPUOpenMaterialX_Renders')
        loader.writeMaterialPreviewFile(outputFolder, 'GPUOpenMaterialX_Previews')

    # Create a test expression
    searchExpr = ''
    if opts.extractExpression:
        searchExpr = opts.extractExpression
    if len(searchExpr) == 0:
        if opts.extractExpression:
            logger.info(f'> No search expression given.')
    else:    
        dataItems = loader.downloadPackageByExpression(searchExpr, 0)
        toMB = 1.0 / (1024.0 * 1024.0)
        unzipFile = opts.unzip if opts.unzip else False
        for dataItem in dataItems:
            data = dataItem[0]
            title = dataItem[1]
            url = dataItem[2]
            logger.info(f'Write package data to file: {title}, Data size: {len(data)*toMB:.2f} MB')
            loader.writePackageDataToFile(data, outputFolder, title, url, unzipFile=unzipFile)    

    extractIndices = opts.extractIndices
    if len(extractIndices) > 0:
        indices = extractIndices.split(',')
        if len(indices) != 3:
            logger.error(f'Error: Invalid indices given: {extractIndices}')
        else:
            materialList = int(indices[0])
            materialIndex = int(indices[1])
            materialPackage = int(indices[2])
            [data, title, url] = loader.downloadPackage(materialList, materialIndex, materialPackage)
            logger.info(f'> Download material: {title} List: {materialList}. Index: {materialIndex}. Package: {materialPackage}. Preview URL:{url}')
            if data:
                loader.writePackageDataToFile(data, outputFolder, title, url)    

    if opts.materialNames:
        materialNamesFile = os.path.join(outputFolder, 'GPUOpenMaterialX_Names.json')
        logger.info(f'> Save materials names to file: {materialNamesFile}')
        sorted = True
        loader.writeMaterialNamesToFile(materialNamesFile, sorted)

if __name__ == '__main__':
    GPUOpenLoaderCmd()