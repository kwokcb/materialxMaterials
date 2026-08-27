'''
@brief Utilities to query and fetch asset information from the 3Dassets.one search engine API.

See: https://3dassets.one/about-site for information on available API calls.
'''
import logging as lg

from http import HTTPStatus
import requests # type: ignore
import os # type: ignore
import inspect # type: ignore

import json # type: ignore
from typing import Optional

class AssetOneLoader:
    '''
    @brief Class to query the 3Dassets.one search engine API.
    The class can search the asset database and query the available types,
    creators and the RSS feed of newly indexed assets.
    '''
    def __init__(self):
        '''
        @brief Constructor for the AssetOneLoader class. 
        Will initialize the API endpoints used to query the 3Dassets.one site.
        '''

        ### logger is the logging object for the class
        self.logger = lg.getLogger('AssetOneLoader')
        lg.basicConfig(level=lg.INFO)

        ### Base URL for the 3Dassets.one v2 API
        self.base_url = 'https://3dassets.one/api/v2'

        ### API endpoints
        self.assets_endpoint = f'{self.base_url}/assets'
        self.types_endpoint = f'{self.base_url}/types'
        self.creators_endpoint = f'{self.base_url}/creators'
        self.assets_rss_endpoint = f'{self.base_url}/assets-rss'

        # Query results
        ### Search result assets
        self.assets : Optional[list] = []
        ### Asset types
        self.types : Optional[list] = []
        ### Asset creators
        self.creators : Optional[list] = []
        ### RSS feed of newly indexed assets
        self.assets_rss = None

        ### List of asset names
        self.assetNames : list[str] = []

    def setDebugging(self, debug : Optional[bool]=True):
        '''
        @brief Set the debugging level for the logger.
        @param debug True to set the logger to debug level, otherwise False.
        @return None
        '''
        if debug:
            self.logger.setLevel(lg.DEBUG)
        else:
            self.logger.setLevel(lg.INFO)

    @staticmethod
    def _getMethodName():
        '''
        @brief Get the name of the calling method. Used for logging.
        @return The name of the calling method.
        '''
        return inspect.stack()[1][3]

    def getAssetNames(self, key='id') -> list:
        ''' 
        @brief Get the list of asset names from the current search results.     
        @param key The key to use for the asset name. Default is 'id'.
        @return The list of asset names
        '''
        self.assetNames.clear()
        unique_names = set()
        if self.assets:
            for item in self.assets:
                unique_names.add(item.get(key))
        self.assetNames = list(sorted(unique_names))
        return self.assetNames

    def findAsset(self, assetId, key='id'):
        '''
        @brief Get the list of assets matching an asset identifier from the current search results.
        @param assetId Asset string identifier
        @param key The key to lookup asset identifiers. Default is 'id'.
        @return List of assets, or None if not found
        '''
        if self.assets:
            assetList = [item for item in self.assets if item.get(key) == assetId]
            return assetList
        return None

    def writeAssetList(self, assetList, filename):
        '''
        @brief Write the asset list in JSON format to a file
        @param assetList The list of assets to write
        @param filename The file path to write the list to
        @return None
        '''
        self.logger.info(f'> {self._getMethodName()}: Writing asset list to file: {filename}')
        with open(filename, mode='w', encoding='utf-8') as json_file:
            json.dump(assetList, json_file, indent=4)

    def writeJsonToFile(self, data, filename):
        '''
        @brief Write arbitrary JSON data to a file
        @param data The data to write
        @param filename The file path to write the data to
        @return None
        '''
        self.logger.info(f'> {self._getMethodName()}: Writing JSON data to file: {filename}')
        with open(filename, mode='w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4)

    def searchAssets(self, query='', assetIds : Optional[list] = None, creators : Optional[list] = None, 
                     types : Optional[list] = None, limit=150, offset=0, sort='popular',
                     thumbnailFormat='256-PNG'):
        '''
        @brief Search the 3Dassets.one asset database.
        @param query The search string, a list of tags.
        @param assetIds List of specific asset ids to search for. 
        @param creators List of creator slugs to filter by. Check the /creators endpoint for valid values.
        @param types List of asset type slugs to filter by. Check the /types endpoint for valid values.
        @param limit Number of assets to return. Default is 150, maximum is 500 per request.
        @param offset Shifts the results to allow pagination.
        @param sort The sorting order of the result. Possible values are: popular, latest, oldest, random,
        most-clicked, least-clicked, most-tagged, least-tagged, oldest-validation-success, latest-validation-success.
        @param thumbnailFormat The format used in the thumbnailUrl field. Possible values are:
        128-PNG, 256-PNG, 128-JPG-FFFFFF, 256-JPG-FFFFFF.
        @return The list of assets returned by the API, or None on error
        '''
        # Build the query parameters
        parameters = {
            'limit': limit,
            'offset': offset,
            'sort': sort,
            'thumbnail-format': thumbnailFormat,
        }
        # Add the search string if specified
        if len(query) > 0:
            parameters['q'] = query

        # Add the repeatable filters
        if assetIds:
            parameters['id[]'] = assetIds
        if creators:
            parameters['creator[]'] = creators
        if types:
            parameters['type[]'] = types

        self.logger.info(f'> {self._getMethodName()}: Searching assets: {parameters}')
        response = requests.get(self.assets_endpoint, params=parameters)

        if response.status_code == HTTPStatus.OK:
            assets = response.json()
            self.assets = assets
            self.logger.info(f'> {self._getMethodName()}: Found {len(assets)} assets')
        else:
            self.assets = None
            self.logger.error(f'> {self._getMethodName()}: Status: {response.status_code}, {response.text}')

        return self.assets

    def downloadTypes(self):
        '''
        @brief Download the list of asset types currently featured on 3Dassets.one.
        This endpoint does not accept any parameters.
        @return The list of asset types, or None on error
        '''
        self.logger.info(f'> {self._getMethodName()}: Downloading types')
        response = requests.get(self.types_endpoint)

        if response.status_code == HTTPStatus.OK:
            types = response.json()
            self.types = types
            self.logger.info(f'> {self._getMethodName()}: Found {len(types)} types')
        else:
            self.types = None
            self.logger.error(f'> {self._getMethodName()}: Status: {response.status_code}, {response.text}')

        return self.types

    def downloadCreators(self):
        '''
        @brief Download the list of creators currently featured on 3Dassets.one.
        This endpoint does not accept any parameters.
        @return The list of creators, or None on error
        '''
        self.logger.info(f'> {self._getMethodName()}: Downloading creators')
        response = requests.get(self.creators_endpoint)

        if response.status_code == HTTPStatus.OK:
            creators = response.json()
            self.creators = creators
            self.logger.info(f'> {self._getMethodName()}: Found {len(creators)} creators')
        else:
            self.creators = None
            self.logger.error(f'> {self._getMethodName()}: Status: {response.status_code}, {response.text}')

        return self.creators

    def downloadAssetsRSS(self):
        '''
        @brief Download the customizable RSS feed of newly indexed assets.
        Filters from the regular /assets endpoint can be used here as well.
        @return The RSS feed content as a string, or None on error
        '''
        self.logger.info(f'> {self._getMethodName()}: Downloading assets RSS feed')
        response = requests.get(self.assets_rss_endpoint)

        if response.status_code == HTTPStatus.OK:
            self.assets_rss = response.text
            self.logger.info(f'> {self._getMethodName()}: Downloaded assets RSS feed')
        else:
            self.assets_rss = None
            self.logger.error(f'> {self._getMethodName()}: Status: {response.status_code}, {response.text}')

        return self.assets_rss
