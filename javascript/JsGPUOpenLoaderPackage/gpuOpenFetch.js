/*
 * Sample script to fetch materials from the GPUOpen Material Library
 * and download the first package.
 * Usage:
 *  npm start -- <arguments> 
 * or
 *  node gpuOpenFetch.js <arguments>
 * or globally after installing the package:
 *  npm install -g .
 *  gpuOpenFetch <arguments>
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

// Create an loader instance
const materialLoader = require('../JsGPUOpenLoader');

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
            if (!data) {
                console.error('Error downloading material:', title);
                continue;
            }
            if (!title) {
                console.error('Error downloading material: No title provided for expression:', expression);
                continue;
            }
            console.log(`Fetched material ${title} package (${data.byteLength} bytes) for expression: ${expression}`);
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
        default: -1
    })
    .option('packageIndex', {
        alias: 'p',
        type: 'number',
        description: 'Index of the package to download',
        default: -1
    })
    .option('getInfo', {
        alias: 'g',
        type: 'boolean',
        description: 'Flag to call getMaterialInformation',
        default: false
    })
    .option('outputFilename', {
        alias: 'o',
        type: 'string',
        description: 'Filename to save the fetched materials',
        default: 'gpuOpenMaterials.json'
    })    
    .help()
    .argv;

// Check if we are fetching material information or downloading a package
if (argv.getInfo) 
{
    console.log('> Fetching material information --');
    getMaterialInformation(argv.batchSize, argv.outputFilename);
} 
else if (argv.materialName.length > 0) {
    let materialName = argv.materialName
    console.log('> Fetch materials matching expression:', argv.materialName);
    downloadMaterialByExpression(argv.materialName, 0);
}
else if (argv.materialIndex >= 0 && argv.packageIndex >= 0)
{
    console.log('> Fetching material matching list index:', argv.materialList, ' material index:', argv.materialIndex, ' package index:', argv.packageIndex);
    downloadMaterial(argv.materialList, argv.materialIndex, argv.packageIndex);
}
else {
    console.log('> No action specifieid to perform. Use --help for usage information.');
}
