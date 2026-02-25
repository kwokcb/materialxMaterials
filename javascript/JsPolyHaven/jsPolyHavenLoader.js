/**
 * JsPolyHavenAPILoader - A JavaScript class for interacting with the Poly Haven API
 * Handles fetching materials, material details, and downloading MaterialX packages
 */
class JsPolyHavenAPILoader {
    /**
     * Constructor for JsPolyHavenAPILoader
     */
    constructor() {
        this.baseUrl = "https://api.polyhaven.com";
        this.userAgent = "MTLX_Polyhaven_Loader/1.0";
    }

    /**
     * Fetch all materials from Poly Haven API
     * @returns {Promise<Array>} Array of processed material objects
     */
    async fetchMaterials() {
        try {
            const response = await fetch(`${this.baseUrl}/assets?t=textures`, {
                headers: { "User-Agent": this.userAgent }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return this.processMaterialsData(data);
        } catch (error) {
            console.error('Error fetching materials:', error);
            throw error;
        }
    }

    /**
     * Process raw materials data from API into structured format
     * @param rawData - Raw data from API
     * @returns Processed materials array
     */
    processMaterialsData(rawData) {
        const materials = [];
        const categories = new Set();

        for (const [id, materialData] of Object.entries(rawData)) {
            // Skip materials without required data
            if (!materialData.name || !materialData.categories) continue;

            // Process authors
            let authorsList = 'Author(s): ';
            const authors = materialData.authors || {};
            const authorNames = Object.keys(authors);
            authorsList += authorNames.join(', ');

            let max_resolution = materialData.max_resolution
            let maxresolutionString = '';
            if (max_resolution) {
                maxresolutionString = `${max_resolution[0]} x ${max_resolution[1]}`
            }

            const material = {
                id,
                name: materialData.name,
                description: authorsList,
                categories: materialData.categories,
                tags: materialData.tags || [],
                thumb_url: `https://cdn.polyhaven.com/asset_img/thumbs/${id}.png?width=512`,
                maps: materialData.maxresolutionString || {}
            };

            materials.push(material);

            // Collect categories
            material.categories.forEach(cat => categories.add(cat));
        }

        return { materials, categories };
    }

    /**
     * Fetch MaterialX files data for a specific material
     * @param materialId - The material ID
     * @returns MaterialX files data
     */
    async fetchMaterialFiles(materialId) {
        try {
            const response = await fetch(`${this.baseUrl}/files/${materialId}`, {
                headers: { "User-Agent": this.userAgent }
            });

            if (!response.ok) {
                throw new Error(`Failed to fetch MaterialX data for ${materialId}`);
            }

            const result = await response.json();
            console.log(`Fetched MaterialX files for ${materialId}:`, result);
            return result;
        } catch (error) {
            console.error(`Error fetching material files for ${materialId}:`, error);
            throw error;
        }
    }

    /**
     * Download MaterialX content from URL
     * @param url - MaterialX file URL
     * @returns MaterialX file content
     */
    async downloadMaterialXContent(url) {
        try {
            const response = await fetch(url, {
                headers: { "User-Agent": this.userAgent }
            });

            if (!response.ok) {
                throw new Error('Failed to download MaterialX file');
            }

            const result = await response.text();
            // Find 
            return result;
        } catch (error) {
            console.error('Error downloading MaterialX content:', error);
            throw error;
        }
    }

    /**
     * Download a texture file from URL
     * @param url - Texture file URL
     * @returns Texture file blob
     */
    async downloadTexture(url) {
        try {
            const response = await fetch(url, {
                headers: { "User-Agent": this.userAgent }
            });

            if (!response.ok) {
                throw new Error(`Failed to download texture from ${url}`);
            }
            else {
                //console.log(`>  Successfully downloaded texture from ${url}`);
            }

            return await response.blob();
        } catch (error) {
            console.error(`Error downloading texture from ${url}:`, error);
            throw error;
        }
    }

    /**
     * Download thumbnail image
     * @param thumbnailUrl Thumbnail URL
     * @returns Thumbnail blob
     */
    async downloadThumbnail(thumbnailUrl) {
        try {
            const response = await fetch(thumbnailUrl, {
                headers: { "User-Agent": this.userAgent }
            });

            if (!response.ok) {
                throw new Error('Failed to download thumbnail');
            }

            return await response.blob();
        } catch (error) {
            console.error('Error downloading thumbnail:', error);
            throw error;
        }
    }

    /**
     * Create a complete MaterialX package with all textures
     * @param material Material object
     * @param resolution Resolution (1k, 2k, 4k, 8k)
     * @returns ZIP file blob containing the complete package
     */
    async createMaterialXPackage(material, resolution, preFetchedData = null) {

        async function downloadWithConcurrency(tasks, concurrency = 3) {
            const results = [];
            const queue = tasks.slice();
            async function worker() {
                while (queue.length) {
                    const task = queue.shift();
                    results.push(await task());
                }
            }
            await Promise.all(Array(concurrency).fill().map(worker));
            return results;
        }

        async function blobToUint8Array(blob) {
            return new Uint8Array(await blob.arrayBuffer());
        }

        try {
            let filesData, mtlxData, mtlxContent, textureFiles;
            if (preFetchedData) {
                mtlxContent = preFetchedData.mtlxContent;
                textureFiles = preFetchedData.textureFiles;
            } else {
                filesData = await this.fetchMaterialFiles(material.id);
                mtlxData = filesData.mtlx?.[resolution]?.mtlx;
                if (!mtlxData) throw new Error(`No MaterialX files for ${resolution}`);
                mtlxContent = await this.downloadMaterialXContent(mtlxData.url);
                textureFiles = mtlxData.include || {};
            }


            // Fetch MaterialX files data
            //const filesData = await this.fetchMaterialFiles(material.id);
            //const mtlxData = filesData.mtlx?.[resolution]?.mtlx;
            console.log('> createMaterialXPackage - fetched MaterialX data:', mtlxData);

            //if (!mtlxData) {
            //    throw new Error(`No MaterialX files found for ${resolution} resolution`);
            //}

            // Zip contents
            const zip = {} 

            // 1. Download and add the main MaterialX file
            //let mtlxContent = await this.downloadMaterialXContent(mtlxData.url);

            // 2. Download and add all included texture files
            //const textureFiles = mtlxData.include || {};
            let texturePaths = [];
            let blobs = {};
            
            //const texturePromises = Object.entries(textureFiles).map(async ([path, fileData]) => {
            const texturePromises = Object.entries(textureFiles).map(([path, fileData]) => async () => 
            {
                try {
                    console.log(`Processing texture: ${path} from URL: ${fileData.url}`);

                    let isEXR = path.toLowerCase().endsWith('.exr');
                    if (isEXR) {
                        const prevPath = path;
                        path = path.replace(/\.exr$/i, '.png');
                        fileData.url = fileData.url.replace(/\/exr\//i, '/png/');
                        fileData.url = fileData.url.replace('.exr', '.png');
                        const previousMtlxContent = mtlxContent;
                        mtlxContent = previousMtlxContent.replace(prevPath, path);
                        console.log(`EXR file detected. Path: ${prevPath} -> ${path}, URL: ${fileData.url}`);
                        if (previousMtlxContent !== mtlxContent) {
                            console.log(`Updated MaterialX content to replace .exr with .png for texture: ${path}`);
                        }
                    }

                    const textureBlob = await this.downloadTexture(fileData.url);

                    texturePaths.push(path);

                    // Build the local path for the zip (preserving folder structure)
                    const pathParts = path.split('/');
                    const localPath = pathParts.join('/');

                    blobs[localPath] = await blobToUint8Array(textureBlob);

                } catch (error) {
                    console.error(`Error downloading texture ${path}:`, error);
                    // Optionally add a placeholder or skip
                }
            });
            await downloadWithConcurrency(texturePromises, 3);
            
            for (const [localPath, blobData] of Object.entries(blobs)) {
                zip[localPath] = blobData;
                console.log(`Added texture to ZIP: ${localPath}`);
            }

            // 3. Download and add thumbnail
            if (material.thumb_url) {
                try {
                    const thumbBlob = await this.downloadThumbnail(material.thumb_url);
                    const thumbUrl = new URL(material.thumb_url);
                    const thumbPath = thumbUrl.pathname.split('/').pop();
                    const thumbExt = thumbPath.split('.').pop();
                    console.log('Add thumbnail to ZIP:', thumbPath);
                    zip[`${material.id}_thumbnail.${thumbExt}`] = await blobToUint8Array(thumbBlob);
                } catch (error) {
                    console.error('Error downloading thumbnail:', error);
                }
            }

            // Wait for all downloads to complete
            await Promise.all(texturePromises);

            for (const textureName of texturePaths) {
                // Patch bad MTLX references in original file
                const extenson = textureName.split('.').pop();
                const exrName = textureName.replace(`.${extenson}`, `.exr`);
                if (mtlxContent.includes(exrName)) {
                    console.log(`Replace ${exrName} with ${textureName} in MaterialX content for preview`);
                    mtlxContent = mtlxContent.replace(exrName, textureName);
                }
            }

            // Add Materialx document to ZIP. 
            // This must be done after texture processing which may
            // modify the MTLX image references.
            console.log(`Adding MaterialX file to ZIP: ${material.id}.mtlx`);
            zip[`${material.id}.mtlx`] =  fflate.strToU8(mtlxContent);
            console.log(`Added MaterialX file to ZIP: ${material.id}.mtlx`); //, ${mtlxContent}`);

            // Add README file, and thumbnail to root of ZIP
            console.log('Adding README.txt to ZIP with material metadata and file list');
            zip["README.txt"] = fflate.strToU8(
                `Material: ${material.name}\n` +
                `Resolution: ${resolution}\n` +
                `Source: https://polyhaven.com/a/${material.id}\n` +
                `Downloaded: ${new Date().toISOString()}\n\n` +
                `Contains the following files:\n` +
                `- ${material.id}.mtlx\n` +
                (material.thumb_url ? `- ${material.id}_thumbnail.png\n` : '') 
                //(texturePaths.length > 0 ? texturePaths.map(t => `- ${t}`).join('\n') + '\n' : '')
            );

            for (const [k, v] of Object.entries(zip)) {
                if (v === zip) {
                    console.error("Circular reference detected in zip at key:", k);
                }
                else
                {
                    console.log(`ZIP entry: ${k}, size: ${v.length || v.size || 'unknown'}`);
                }
            }

             // Compress the ZIP file
            console.log('Compressing ZIP file with fflate...');
            const zipped = fflate.zipSync(zip);

            // Create a Blob from the zipped data
            console.log('Creating Blob from zipped data...');
            const blob = new Blob([zipped], { type: 'application/zip' });     
            
            console.log('MaterialX package created successfully:', blob);
            return blob;

        } catch (error) {
            console.error('Error creating MaterialX package:', error);
            throw error;
        }
    }

    /**
     * Get MaterialX content and texture files for preview
     * @param materialId Material ID
     * @param resolution Resolution (1k, 2k, 4k, 8k)
     * @returns Object containing MaterialX content and texture files
     */
    async getMaterialContent(materialId, resolution) {
        try {
            const filesData = await this.fetchMaterialFiles(materialId);
            const mtlxData = filesData.mtlx?.[resolution]?.mtlx;

            if (!mtlxData) {
                throw new Error(`No MaterialX files found for ${resolution} resolution`);
            }

            // Get MaterialX content
            const mtlxContent = await this.downloadMaterialXContent(mtlxData.url);

            return {
                mtlxContent,
                textureFiles: mtlxData.include || {}
            };
        } catch (error) {
            console.error('Error getting material content:', error);
            throw error;
        }
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = JsPolyHavenAPILoader;
} else if (typeof window !== 'undefined') {
    window.JsPolyHavenAPILoader = JsPolyHavenAPILoader;
}
