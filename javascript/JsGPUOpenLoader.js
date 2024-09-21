/**
 * @class JsGPUOpenMaterialLoader
 * @brief Class to download MaterialX materials from the GPUOpen material database.
 * The class provides methods to fetch materials and download material packages.
 * The class uses the fetch API to make HTTP requests.
 * The class is intended to be used in a Node.js environment.
 */
class JsGPUOpenMaterialLoader {
    /**
     * Constructor for the JsGPUOpenMaterialLoader class.
     */
    constructor() {
        this.rootUrl = 'https://api.matlib.gpuopen.com/api';
        this.url = `${this.rootUrl}/materials`;
        this.packageUrl = `${this.rootUrl}/packages`;
        this.materials = null;
        this.materialNames = null;

        this.logger = console;
    }

    /** 
     * Return downloaded material list
     * @return {Array} - List of materials
     */    
    getMaterialList() {
        return this.materials;
    }

    /**
     * Return downloaded material names
     * @return {Array} - List of material names
     */
    getMaterialNames() {
        return this.materialNames;
    }

    /**
     * Get lists of materials from the GPUOpen material database.
     * @param {number} batchSize - Number of materials to fetch per batch
     * @return {Array} - List of material lists
     */
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
                
                //console.log("Number of materials fetched:", jsonData.results.length)

                let nextURL = jsonData.next
                if (nextURL) {
                    //console.log('Next URL: ', jsonData.next)
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

    /**
     * Download a material package from the GPUOpen material database.
     * @param {number} listNumber - Index of the material list
     * @param {number} materialNumber - Index of the material in the list
     * @param {number} packageId - Index of the package in the material
     * @return {Array} - A list containing the package data and title
     */
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
        //console.log(`Package size: ${data.byteLength} bytes`);        
        return [data, title];
    }

    /**
     * Find materials by name.
     * @param {string} materialName - Regular expression to match the material name.
     * @return {Array} - A list of materials that match the regular expression of the form:
     * [{ 'listNumber': listNumber, 'materialNumber': materialNumber, 'title': title }]
     */
    findMaterialsByName(materialName) 
    {
        if (!this.materials) {
            return [];
        }

        const materialsList = [];
        let listNumber = 0;
        
        // Create a RegExp object for case-insensitive matching
        const regex = new RegExp(materialName, 'i');
        
        this.materials.forEach((materialList, materialIndex) => {
            let materialNumber = 0;

            materialList['results'].forEach((material) => {

                //console.log('testing material:', material['title'], ' with regex:', regex)
                if (regex.test(material['title'])) {
                    materialsList.push({
                        listNumber: listNumber,
                        materialNumber: materialNumber,
                        title: material['title'],
                    });
                }
                materialNumber += 1;
            });

            listNumber += 1;
        });

        return materialsList;
    }        

    /**
     * Download a material package by string expression.
     * @param {string} searchExpr - Regular expression to match the material name
     * @param {number} packageId - Index of the package in the material
     * @return {Array} - A list of material items that match the regular expression of the form:
     * [[data, title], [data, title], ...]
     * where data is the package data (in zip form) and title is the material title
     */
    async downloadPackageByExpression(searchExpr, packageId = 0) {
        const downloadList = [];

        const foundList = this.findMaterialsByName(searchExpr);
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

module.exports = { JsGPUOpenMaterialLoader };
