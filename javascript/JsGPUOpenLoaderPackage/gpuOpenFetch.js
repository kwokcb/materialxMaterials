/*
 * Sample script to fetch materials from the GPUOpen Material Library
 * and download the first package.
 * Usage:
 *  npm start -- <arguments> 
 * or
 *  node gpuOpenFetch.js <arguments>
 */

const fs = require('fs');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');

async function testFetch() 
/* 
 * Sample code
 */
{
    const fetch = require('node-fetch');  
    async function fetchMaterials() {
        const response = await fetch('https://api.matlib.gpuopen.com/api/materials/');
        const json = await response.json();
        console.log('Fetched:', json.results.length, 'materials');
    }
 
    fetchMaterials().catch(error => console.error('Error:', error));
}

 // Import the loader class
const { MxGPUOpenMaterialLoader } = require('./JsGPUOpenLoader'); 

// Create an loader instance
const materialLoader = new MxGPUOpenMaterialLoader();

// Get materials
async function getMaterialInformation(batchSize=50, fileName="gpuOpenMaterials.json") {
    try {
        // Get all materials
        const materials = await materialLoader.getMaterials(batchSize);
        const materialNames = materialLoader.getMaterialNames()
        console.log('Fetched materials:', materialNames.length);

        if (fileName.length == 0) {
            return;
        }
        // Save each JSON object in materials to disk
        fs.writeFileSync(fileName, JSON.stringify(materials, null, 2));
        console.log('Wrote material information to:', fileName);
        let materialsNamesFile = fileName.replace('.json', '_names.json');
        fs.writeFileSync(materialsNamesFile, JSON.stringify(materialNames, null, 2));
        console.log('Wrote material names to:', materialsNamesFile);

        if (materialNames.length === 0) {
            console.error('No materials found');
            return;
        }
    } catch (error) {
        console.error('Error fetching materials:', error);
    }
}

// Download a material from list
async function downloadMaterial(listNumber=0, materialNumber=0, packageId = 0) {
    try {
        await getMaterialInformation(100, "");
        let [data, title] = await materialLoader.downloadPackage(listNumber, materialNumber, packageId)
        if (!data) {
            console.error('Error downloading material:', title);
            return;
        }

        let filename = title.replace(/[^a-z0-9]/gi, '_') + '.zip';
        fs.writeFileSync(filename, Buffer.from(data));    
        console.log(`Wrote material ${title} package (${data.byteLength} bytes) to: ${filename}`);
        return ;        
    } catch (error) {
        console.error('Error fetching materials:', error);
    }
}

// Download a material by expression
async function downloadMaterialByExpression(expression = '', packageIndex = 0) {
    if (expression.length === 0) {
        console.error('No material expression provided');
        return;
    }

    try {
        await getMaterialInformation(100, "");
        let dataItems = await materialLoader.downloadPackageByExpression(expression, packageIndex)
        if (!dataItems) {
            console.error('Error downloading material:', expression);
            return;
        }

        for (const dataItem of dataItems) 
        {
            const [data, title] = dataItem;
            let filename = title.replace(/[^a-z0-9]/gi, '_') + '.zip';
            fs.writeFileSync(filename, Buffer.from(data));    
            console.log(`Wrote material ${title} package (${data.byteLength} bytes) to: ${filename}`);
        }
        return ;        
    } catch (error) {
        console.error('Error fetching materials:', error);
    }
}

const argv = yargs(hideBin(process.argv))
    .option('materialName', {
        alias: 'n',
        type: 'string',
        description: 'Name of the material to fetch',
        default: ''
    })
    .option('batchSize', {
        alias: 'b',
        type: 'number',
        description: 'Batch size for fetching materials',
        default: 50
    })
    .option('materialList', {
        alias: 'l',
        type: 'number',
        description: 'Index of the material list',
        default: 0
    })
    .option('materialIndex', {
        alias: 'i',
        type: 'number',
        description: 'Index of the material in the list',
        default: 0
    })
    .option('packageIndex', {
        alias: 'p',
        type: 'number',
        description: 'Index of the package to download',
        default: 0
    })
    .option('getInfo', {
        alias: 'g',
        type: 'boolean',
        description: 'Flag to call getMaterialInformation',
        default: true
    })
    .option('outputFilename', {
        alias: 'o',
        type: 'string',
        description: 'Filename to save the fetched materials',
        default: 'gpuOpenMaterials.json'
    })    
    .help()
    .argv;

console.log(argv)

// Check if we are fetching material information or downloading a package
let materialName = argv.materialName
console.log('Material name:', argv.materialName)
if (argv.materialName.length > 0) {
    console.log('------------- Look for material:', argv.materialName);
    downloadMaterialByExpression(argv.materialName, argv.packageIndex);
}
else {
    if (argv.getInfo) 
    {
        console.log('-- Fetching material information --');
        getMaterialInformation(argv.batchSize, argv.outputFilename);
    } 
    else 
    {
        console.log('-- Fetching material --');
        downloadMaterial(argv.materialList, argv.materialIndex, argv.packageIndex);
    }
}