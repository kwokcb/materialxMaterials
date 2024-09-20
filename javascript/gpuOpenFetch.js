/*
 * Sample script to fetch materials from the GPUOpen Material Library
 * and download the first package.
 */

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
async function loadMaterials() {
    try {
        // Get all materials
        const materials = await materialLoader.getMaterials();
        const materialNames = materialLoader.getMaterialNames()
        console.log('Fetched materials:', materialNames.length);

        if (materialNames.length === 0) {
            console.error('No materials found');
            return;
        }
        // Download the first package
        materialLoader.downloadPackage(0, 0)
    } catch (error) {
        console.error('Error fetching materials:', error);
    }
}

// Call the function
loadMaterials()