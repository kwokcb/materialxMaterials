#/usr/bin/env python3
'''
@brief Command to download ambientCG MaterialX materials'''

import os, argparse, sys, logging
import ambientCGLoader as acg
import MaterialX as mx

def ambientCgLoaderCmd():
    '''
    Utility to download ambientCG MaterialX materials
    '''
    logger = logging.getLogger('ACG_CMD')
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description='Get materials information and material package from ambientCG.'
                                     ' By default the materials will be downloaded and a named and index material'
                                     ' package will be extracted.')

    parser.add_argument('--loadMaterials', type=str, default='', 
                        help='Load JSON file containing list of materials that can be downloaded.')
    parser.add_argument('--downloadMaterials', type=bool, default=None, 
                        help='Download JSON file containing list of materials that can be downloaded.'
                        ' Has no effect if --loadMaterials is set')    

    # Material names query
    parser.add_argument('--materialNames', type=bool, default=None,
                        help='Return material names. Default is False')
    
    # Save download information for all materials or a specific one
    # based on asset identifier 
    parser.add_argument('-sms', '--saveMaterials', type=bool, default=None, 
                        help='Save material lists. Default is None.'
                        ' Has no effect if --loadMaterials is set')    
    parser.add_argument('-sm', '--saveMaterial', type=str, default='', 
                        help='Save material download information in JSON format')

    # Asset download options
    parser.add_argument('-m', '--downloadMaterial', type=str, default='', 
                        help='Download zip package for a materials which match a given string. Default is a sample material')
    parser.add_argument('-f', '--downloadmageFormat', type=str, default='PNG', 
                        help='Download image format. Valid values include PNG and JPEG. Default is PNG')
    parser.add_argument('-r', '--downloadResolution', type=str, default='1', 
                        help='Download image resulution. Valid values include 1,2,4,8 to indicate 1K to 8K.')

    # Download full database iformation for material assets
    parser.add_argument('-dd', '--downloadDatabase', type=bool, default=None, 
                        help='Download information database')
    parser.add_argument('-sd', '--saveDatabase', type=str, default='ambientCG_database.json', 
                        help='Save information database')

    # Output options
    parser.add_argument('--output', type=str, default='', 
                        help='Output folder for data files. Default location is the current execution folder.')
    opts = parser.parse_args()

    loader = acg.AmbientCGLoader(mx, None)
    
    # Set output folder. Default is current folder
    outputFolder = '.'
    if opts.output:
        outputFolder = opts.output
    if not os.path.exists(outputFolder):
        logger.error(f'Output directory does not exist: {outputFolder}')
        sys.exit(1)
    
    # Get materials list which contains download information
    loadMaterials = opts.loadMaterials
    downloadMaterials = opts.downloadMaterials or opts.saveMaterials
    if loadMaterials or downloadMaterials:
        materialsList = None
        if len(loadMaterials) > 0:
            materialsList = loader.loadMaterialsList(loadMaterials)
        elif downloadMaterials:
            materialsList = loader.downloadMaterialsList()
            # Save materials list if specified. Only do so for download case
            if opts.saveMaterials:
                loader.writeMaterialList(materialsList, os.path.join(outputFolder,'ambientCG_materialsList.json'))

        # Check if the list of materials is asked to be returned
        if opts.materialNames:
            materialNames = loader.getMaterialNames()
            print(f'{materialNames}')        

        # Check if a material asset is specified to downloaded  
        materialName = opts.downloadMaterial
        if len(materialName) > 0:
            result = loader.findMaterial(materialName)
            if result:
                fileName = loader.downloadMaterialAsset(materialName, opts.downloadmageFormat, opts.downloadResolution)
                if len(fileName) > 0:
                    loader.writeDownloadedMaterialToFile(outputFolder)
            else:
                print(f'Material not found: {materialName}')      

    # Check if material database is specified for download
    databaseFileName = opts.saveDatabase
    haveDatabaseFileName = len(databaseFileName) > 0
    downloadDatabase = opts.downloadDatabase and haveDatabaseFileName
    if downloadDatabase:
        print('download database')
        loader.downloadAssetDatabase()        
        if haveDatabaseFileName:
            path = os.path.join(outputFolder, databaseFileName)
            loader.writeDatabaseToFile(path)    

if __name__ == '__main__':
    ambientCgLoaderCmd()