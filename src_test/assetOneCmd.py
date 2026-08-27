#/usr/bin/env python3
'''
@brief Command to query the 3Dassets.one API for asset search information'''
import os, argparse, sys, logging
import assetOne as aone

def assetOneLoaderCmd():
    '''
    Utility to query the 3Dassets.one API
    '''
    logger = logging.getLogger('ASSETONE_CMD')
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description='Query asset information from the 3Dassets.one API.'
                                     ' The asset search, types and creators lists can be queried'
                                     ' and saved to JSON files.')

    # Asset search options
    parser.add_argument('-q', '--query', type=str, default='', 
                        help='Search string, a list of tags.')
    parser.add_argument('-id', '--assetIds', type=str, default='', 
                        help='Search for specific asset ids. Comma separated list.')
    parser.add_argument('-c', '--creators', type=str, default='', 
                        help='Search for specific creators using their slug. Comma separated list.')
    parser.add_argument('-t', '--types', type=str, default='', 
                        help='Search for specific types using their slug. Comma separated list.')
    parser.add_argument('-l', '--limit', type=int, default=150, 
                        help='Number of assets returned. Default is 150, maximum is 500 per request.')
    parser.add_argument('-off', '--offset', type=int, default=0, 
                        help='Shifts the results to allow pagination.')
    parser.add_argument('-s', '--sort', type=str, default='popular', 
                        help='Sorting order. Possible values: popular, latest, oldest, random, most-clicked,'
                        ' least-clicked, most-tagged, least-tagged, oldest-validation-success, latest-validation-success.')
    parser.add_argument('-tf', '--thumbnailFormat', type=str, default='256-PNG', 
                        help='Thumbnail format. Possible values: 128-PNG, 256-PNG, 128-JPG-FFFFFF, 256-JPG-FFFFFF.')

    # Information queries
    parser.add_argument('-lt', '--listTypes', type=bool, default=None, 
                        help='Return the list of asset types currently featured on 3Dassets.one.')
    parser.add_argument('-lc', '--listCreators', type=bool, default=None, 
                        help='Return the list of creators currently featured on 3Dassets.one.')
    parser.add_argument('-rss', '--downloadRSS', type=bool, default=None, 
                        help='Return the RSS feed of newly indexed assets.')

    # Save options
    parser.add_argument('-sa', '--saveAssets', type=str, default='', 
                        help='Save the asset search results in JSON format to a specified file.')
    parser.add_argument('-st', '--saveTypes', type=str, default='', 
                        help='Save the types list in JSON format to a specified file.')
    parser.add_argument('-sc', '--saveCreators', type=str, default='', 
                        help='Save the creators list in JSON format to a specified file.')

    # Output options
    parser.add_argument('-o', '--output', type=str, default='', 
                        help='Output folder for data files. Default location is the current execution folder.')
    opts = parser.parse_args()

    loader = aone.AssetOneLoader()
    
    # Set output folder. Default is current folder
    outputFolder = '.'
    if opts.output:
        outputFolder = opts.output
    if not os.path.exists(outputFolder):
        # Create output folder if it doesn't exist
        logger.info(f'Creating output folder: {outputFolder}')
        os.makedirs(outputFolder)

    # Search assets if a query or any filter is specified
    searchAssets = len(opts.query) > 0 or len(opts.assetIds) > 0 or len(opts.creators) > 0 or len(opts.types) > 0
    if searchAssets:
        # Parse the comma separated filter lists
        assetIds = [item.strip() for item in opts.assetIds.split(',') if len(item.strip()) > 0] if opts.assetIds else None
        creators = [item.strip() for item in opts.creators.split(',') if len(item.strip()) > 0] if opts.creators else None
        types = [item.strip() for item in opts.types.split(',') if len(item.strip()) > 0] if opts.types else None

        assets = loader.searchAssets(query=opts.query, assetIds=assetIds, creators=creators, types=types,
                                     limit=opts.limit, offset=opts.offset, sort=opts.sort,
                                     thumbnailFormat=opts.thumbnailFormat)
        if len(opts.saveAssets) > 0:
            output_path = os.path.join(outputFolder, opts.saveAssets)
            logger.info(f'Saving assets to {output_path}')
            loader.writeAssetList(assets, output_path)
        else:
            print(f'{assets}')

    # Query the list of asset types
    if opts.listTypes:
        types = loader.downloadTypes()
        if len(opts.saveTypes) > 0:
            output_path = os.path.join(outputFolder, opts.saveTypes)
            logger.info(f'Saving types to {output_path}')
            loader.writeJsonToFile(types, output_path)
        else:
            print(f'{types}')

    # Query the list of creators
    if opts.listCreators:
        creators = loader.downloadCreators()
        if len(opts.saveCreators) > 0:
            output_path = os.path.join(outputFolder, opts.saveCreators)
            logger.info(f'Saving creators to {output_path}')
            loader.writeJsonToFile(creators, output_path)
        else:
            print(f'{creators}')

    # Query the RSS feed of newly indexed assets
    if opts.downloadRSS:
        rss = loader.downloadAssetsRSS()
        print(f'{rss}')

    # Nothing was requested, show usage information
    if not searchAssets and not opts.listTypes and not opts.listCreators and not opts.downloadRSS:
        logger.info('No operation requested. Use -h or --help for help.')

if __name__ == '__main__':
    assetOneLoaderCmd()
