class GPUOpenMaterialLoader {
    constructor() {
        this.rootUrl = 'https://api.matlib.gpuopen.com/api';
        this.url = `${this.rootUrl}/materials`;
        this.packageUrl = `${this.rootUrl}/packages`;
        this.materials = null;

        this.logger = console;
    }

    async getMaterials() {
        /*
         * Get the materials returned from the GPUOpen material database.
         * Will loop based on the linked-list of materials stored in the database.
         * Currently, the batch size requested is 100 materials per batch.
         * @return: List of material lists
         */
        
        this.materials = [];
        this.materialNames = [];

        let url = this.url;
        const headers = {
            'Accept': 'application/json'
        };

        // Get batches of materials. Start with the first 100.
        let params = new URLSearchParams({
            limit: 100,
            offset: 0
        });

        //url = 'https://api.physicallybased.info/materials'

        let haveMoreMaterials = true;
        while (haveMoreMaterials) 
        {
            try {
                console.log('----- fetch url', url)
                const response = //await fetch(`${url}?${params.toString()}`, { headers });
                await fetch(url, {
                        mode: 'cors',
                        method: 'GET',
                        headers: headers,
                        params: {
                            'limit': 100,
                            'offset': 0
                        }
                })              
                if (response.ok) {
                    const rawResponse = await response.text();

                    // Split the response text assuming the JSON objects are concatenated
                    const jsonStrings = rawResponse.split('}{');
                    let jsonResultString = jsonStrings[0] + (jsonStrings.length > 1 ? '}' : '');
                    const jsonObject = JSON.parse(jsonResultString);
                    this.materials.push(jsonObject);
                    haveMoreMaterials = true;

                    // Scan for next batch of materials
                    const nextQuery = jsonObject['next'];
                    if (nextQuery) {
                        // Get limit and offset from the query string
                        const queryParts = new URL(nextQuery).searchParams;
                        params = new URLSearchParams({
                            limit: queryParts.get('limit') || 100,
                            offset: queryParts.get('offset') || 0
                        });
                        this.logger.info(`Fetch set of materials: limit: ${params.get('limit')} offset: ${params.get('offset')}`);
                    } else {
                        haveMoreMaterials = false;
                        break;
                    }
                } else {
                    this.logger.info(`Error: ${response.status}, ${await response.text()}`);
                    haveMoreMaterials = true;
                }
            } catch (error) {
                this.logger.info(`Error: ${error.message}`);
                haveMoreMaterials = true;
            }

            break;
        }

        return this.materials;
    }    

    async downloadPackage(listNumber, materialNumber, packageId = 0) {
        if (this.materials === null || this.materials.length === 0) {
            return [null, null];
        }

        const jsonData = this.materials[listNumber];
        if (!jsonData) {
            return [null, null];
        }

        let jsonResults = null;
        let jsonResult = null;
        if ('results' in jsonData) {
            jsonResults = jsonData['results'];
            if (jsonResults.length <= materialNumber) {
                return [null, null];
            } else {
                jsonResult = jsonResults[materialNumber];
            }
        }

        if (!jsonResult) {
            return [null, null];
        }

        let jsonPackages = null;
        if ('packages' in jsonResult) {
            jsonPackages = jsonResult['packages'];
        }
        if (!jsonPackages) {
            return [null, null];
        }

        if (jsonPackages.length <= packageId) {
            return [null, null];
        }
        const packageIdValue = jsonPackages[packageId];

        if (!packageIdValue) {
            return [null, null];
        }

        const url = `${this.packageUrl}/${packageIdValue}/download`;
        const response = await fetch(url);
        const data = await response.arrayBuffer();
        const title = jsonResult['title'];
        return [data, title];
    }

    async downloadPackageByExpression(searchExpr, packageId = 0) {
        const downloadList = [];

        const foundList = await this.findMaterialsByName(searchExpr);
        if (foundList.length > 0) {
            for (const found of foundList) {
                const listNumber = found['listNumber'];
                const materialNumber = found['materialNumber'];
                const matName = found['title'];
                this.logger.info(`> Download material: ${matName} List: ${listNumber}. Index: ${materialNumber}`);
                const [data, title] = await this.downloadPackage(listNumber, materialNumber, packageId);
                downloadList.push([data, title]);
            }
        }
        return downloadList;
    }
}
