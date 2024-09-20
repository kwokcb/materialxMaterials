// Use node-fetch in case Node.js does not have fetch
//const fetch = require('node-fetch'); 

class MxGPUOpenMaterialLoader {
    /* 
     * Class to load materials from the GPUOpen material database.
     * The class provides methods to fetch materials and download material packages.
     * The class uses the fetch API to make HTTP requests.
     * The class is intended to be used in a Node.js environment.
     */ 
    constructor() {
        this.rootUrl = 'https://api.matlib.gpuopen.com/api';
        this.url = `${this.rootUrl}/materials`;
        this.packageUrl = `${this.rootUrl}/packages`;
        this.materials = null;
        this.materialNames = null;

        this.logger = console;
    }

    getMaterialList() {
        return this.materials;
    }

    getMaterialNames() {
        return this.materialNames;
    }

    async getMaterials(batchSize = 50) {

        const fetch = (await import('node-fetch')).default;

        /*
         * Get the materials returned from the GPUOpen material database.
         * Will loop based on the linked-list of materials stored in the database.
         * Currently, the batch size requested is 100 materials per batch.
         * @param batchSize: Number of materials to fetch per batch
         * @return: List of material lists
         */
        
        this.materials = [];
        this.materialNames = [];

        let url = this.url;

        // Get batches of materials. Start with the first N.
        let params = new URLSearchParams({
            limit: batchSize,
            offset: 0
        });

        // Append & parameters to url using params
        if (params) {
            url += '?' + params.toString();
        }

        let haveMoreMaterials = true;
        while (haveMoreMaterials) 
        {
            try {

                console.log('Fetch materials from url:', url)

                const response = await fetch(url);

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const jsonData = await response.json(); 
                this.materials.push(jsonData)   

                for (const material of jsonData.results) {
                    this.materialNames.push(material['title']);
                }
                
                console.log("Number of materials fetched:", jsonData.results.length)

                let nextURL = jsonData.next
                if (nextURL) {
                    console.log('Next URL: ', jsonData.next)
                    url = nextURL;
                    haveMoreMaterials = true
                }
                else
                {
                    console.log('Finished fetching materials')
                    haveMoreMaterials = false;
                    break;
                }

            } catch (error) {
                this.logger.info(`Error: ${error.message}`);
                haveMoreMaterials = true;
            }
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

        const fetch = (await import('node-fetch')).default;

        const url = `${this.packageUrl}/${packageIdValue}/download`;
        const response = await fetch(url);
        const data = await response.arrayBuffer();
        const title = jsonResult['title'];

        console.log(`Downloaded package: ${title} from ${url}`);
        console.log(`Package size: ${data.byteLength} bytes`);        
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

module.exports = { MxGPUOpenMaterialLoader };
