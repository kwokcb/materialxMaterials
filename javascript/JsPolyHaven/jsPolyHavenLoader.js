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

            return await response.json();
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

            return await response.text();
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
    async createMaterialXPackage(material, resolution) {
        try {
            // Fetch MaterialX files data
            const filesData = await this.fetchMaterialFiles(material.id);
            const mtlxData = filesData.mtlx?.[resolution]?.mtlx;

            if (!mtlxData) {
                throw new Error(`No MaterialX files found for ${resolution} resolution`);
            }

            // Create ZIP file
            const zip = new JSZip();

            // 1. Download and add the main MaterialX file
            const mtlxContent = await this.downloadMaterialXContent(mtlxData.url);
            zip.file(`${material.id}.mtlx`, mtlxContent);
            console.log(`Added MaterialX file to ZIP: ${material.id}.mtlx, ${mtlxContent}`);

            // 2. Download and add all included texture files
            const textureFiles = mtlxData.include || {};
            const texturePromises = Object.entries(textureFiles).map(async ([path, fileData]) => {
                try {
                    const textureBlob = await this.downloadTexture(fileData.url);
                    
                    // Maintain the folder structure from the include paths
                    const pathParts = path.split('/');
                    let currentFolder = zip;

                    // Handle nested folder structure
                    for (let i = 0; i < pathParts.length - 1; i++) {
                        const folderName = pathParts[i];
                        currentFolder = currentFolder.folder(folderName);
                    }

                    currentFolder.file(pathParts[pathParts.length - 1], textureBlob);

                    if (path.toLowerCase().endsWith('.exr')) {
                        console.warn(`EXR file present which may not be supported by MaterialX texture loader: ${path}`);
                    }
                    else {
                        console.log(`Added texture to ZIP: ${path}`);
                    }
                } catch (error) {
                    console.error(`Error downloading texture ${path}:`, error);
                    // Add placeholder file if download fails
                    zip.file(path, `Failed to download: ${fileData.url}`);
                }
            });

            // 3. Download and add thumbnail
            if (material.thumb_url) {
                try {
                    const thumbBlob = await this.downloadThumbnail(material.thumb_url);
                    const thumbUrl = new URL(material.thumb_url);
                    const thumbPath = thumbUrl.pathname.split('/').pop();
                    const thumbExt = thumbPath.split('.').pop();
                    zip.file(`${material.id}_thumbnail.${thumbExt}`, thumbBlob);
                } catch (error) {
                    console.error('Error downloading thumbnail:', error);
                }
            }

            // Wait for all downloads to complete
            await Promise.all(texturePromises);

            // Add README file
            zip.file("README.txt",
                `Material: ${material.name}\n` +
                `Resolution: ${resolution}\n` +
                `Source: https://polyhaven.com/a/${material.id}\n` +
                `Downloaded: ${new Date().toISOString()}\n\n` +
                `Contains the following files:\n` +
                `- ${material.id}.mtlx\n` +
                Object.keys(textureFiles).map(path => `- ${path}`).join('\n') +
                (material.thumb_url ? `\n- ${material.id}_thumbnail.png` : '')
            );

            // Generate the ZIP file
            return await zip.generateAsync({ type: 'blob' });

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
