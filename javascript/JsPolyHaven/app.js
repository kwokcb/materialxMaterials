// Global variables
let allMaterials = [];
let categories = new Set();
let currentSelectedMaterial = null;
const BASE_API = "https://api.polyhaven.com";

// DOM elements
const materialsContainer = document.getElementById('materialsContainer');
const searchInput = document.getElementById('searchInput');
const searchButton = document.getElementById('searchButton');
const categoryFilter = document.getElementById('categoryFilter');
const resolutionFilter = document.getElementById('resolutionFilter');
const mainSpinner = document.getElementById('mainSpinner');
const materialModal = new bootstrap.Modal(document.getElementById('materialModal'));

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    loadMaterials();
    
    // Event listeners
    searchButton.addEventListener('click', filterMaterials);
    searchInput.addEventListener('keyup', function(e) {
        if (e.key === 'Enter') filterMaterials();
    });
    categoryFilter.addEventListener('change', filterMaterials);
    resolutionFilter.addEventListener('change', filterMaterials);
    
    // Modal buttons
    document.getElementById('downloadMaterial').addEventListener('click', downloadMaterial);
    document.getElementById('copyMaterialLink').addEventListener('click', copyMaterialLink);
    document.getElementById('materialResolution').addEventListener('change', updateMapsDisplay);
});

async function downloadMaterial() {
    if (!currentSelectedMaterial) return;
    
    const resolution = document.getElementById('materialResolution').value;
    const materialId = currentSelectedMaterial.id;
    const materialName = currentSelectedMaterial.name.replace(/[^a-z0-9]/gi, '_').toLowerCase();
    
    // Show loading state
    const downloadBtn = document.getElementById('downloadMaterial');
    const originalText = downloadBtn.innerHTML;
    downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Preparing download...';
    downloadBtn.disabled = true;
    
    try {
        // First fetch the MaterialX data for this asset
        const filesResponse = await fetch(`${BASE_API}/files/${materialId}`, {
            headers: { "User-Agent": "MTLX_Polyhaven_Loader/1.0" }
        });
        if (!filesResponse.ok) throw new Error('Failed to fetch MaterialX data');
        
        const filesData = await filesResponse.json();
        const mtlxData = filesData.mtlx?.[resolution]?.mtlx;
        
        if (!mtlxData) {
            throw new Error(`No MaterialX files found for ${resolution} resolution`);
        }
        
        // Create ZIP file
        const zip = new JSZip();
        
        // 1. Download and add the main MaterialX file
        const mtlxResponse = await fetch(mtlxData.url, {
            headers: { "User-Agent": "MTLX_Polyhaven_Loader/1.0" }
        });
        if (!mtlxResponse.ok) throw new Error('Failed to download MaterialX file');
        
        const mtlxContent = await mtlxResponse.text();
        zip.file(`${materialId}.mtlx`, mtlxContent);
        
        // 2. Download and add all included texture files
        const textureFiles = mtlxData.include || {};
        const texturePromises = Object.entries(textureFiles).map(async ([path, fileData]) => {
            try {
                const textureResponse = await fetch(fileData.url, {
                    headers: { "User-Agent": "MTLX_Polyhaven_Loader/1.0" }
                });
                if (!textureResponse.ok) throw new Error(`Failed to download ${path}`);
                
                const textureBlob = await textureResponse.blob();
                // Maintain the folder structure from the include paths
                const pathParts = path.split('/');
                let currentFolder = zip;
                
                // Handle nested folder structure
                for (let i = 0; i < pathParts.length - 1; i++) {
                    const folderName = pathParts[i];
                    if (!currentFolder.folder(folderName)) {
                        currentFolder = currentFolder.folder(folderName);
                    } else {
                        currentFolder = currentFolder.folder(folderName);
                    }
                }
                
                currentFolder.file(pathParts[pathParts.length - 1], textureBlob);
                
                if (path.toLowerCase().endsWith('.exr')) {
                    console.warn(`EXR file present which may not be supported by MaterialX texture loader: ${path}`);
                }
            } catch (error) {
                console.error(`Error downloading texture ${path}:`, error);
                // Add placeholder file if download fails
                zip.file(path, `Failed to download: ${fileData.url}`);
            }
        });
        
        // 3. Download and add thumbnail
        if (currentSelectedMaterial.thumb_url) {
            try {
                const thumbResponse = await fetch(currentSelectedMaterial.thumb_url, {
                    headers: { "User-Agent": "MTLX_Polyhaven_Loader/1.0" }
                });
                if (thumbResponse.ok) {
                    const thumbBlob = await thumbResponse.blob();
                    const thumbUrl = new URL(currentSelectedMaterial.thumb_url);
                    const thumbPath = thumbUrl.pathname.split('/').pop();
                    const thumbExt = thumbPath.split('.').pop();
                    zip.file(`${materialId}_thumbnail.${thumbExt}`, thumbBlob);
                }
            } catch (error) {
                console.error('Error downloading thumbnail:', error);
            }
        }
        
        // Wait for all downloads to complete
        await Promise.all(texturePromises);
        
        // Add README file
        zip.file("README.txt", 
            `Material: ${currentSelectedMaterial.name}\n` +
            `Resolution: ${resolution}\n` +
            `Source: https://polyhaven.com/a/${materialId}\n` +
            `Downloaded: ${new Date().toISOString()}\n\n` +
            `Contains the following files:\n` +
            `- ${materialId}.mtlx\n` +
            Object.keys(textureFiles).map(path => `- ${path}`).join('\n') +
            (currentSelectedMaterial.thumb_url ? `\n- ${materialId}_thumbnail.png` : '')
        );
        
        // Generate the ZIP file
        const content = await zip.generateAsync({ type: 'blob' });
        
        // Trigger download
        const url = URL.createObjectURL(content);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${materialName}_${resolution}_materialx.zip`;
        document.body.appendChild(a);
        a.click();
        
        // Clean up
        setTimeout(() => {
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }, 100);
        
    } catch (error) {
        console.error('Error creating MaterialX package:', error);
        alert(`Failed to prepare download: ${error.message}`);
    } finally {
        // Restore button state
        downloadBtn.innerHTML = originalText;
        downloadBtn.disabled = false;
    }
}

async function downloadMaterial2() {
    if (!currentSelectedMaterial) return;
    
    const resolution = document.getElementById('materialResolution').value;
    const materialId = currentSelectedMaterial.id;
    const materialName = currentSelectedMaterial.name.replace(/[^a-z0-9]/gi, '_').toLowerCase();
    
    // Show loading state
    const downloadBtn = document.getElementById('downloadMaterial');
    const originalText = downloadBtn.innerHTML;
    downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Preparing download...';
    downloadBtn.disabled = true;
    
    try {
        // First fetch the MaterialX data for this asset
        const filesResponse = await fetch(`${BASE_API}/files/${materialId}`, {
            headers: { "User-Agent": "MTLX_Polyhaven_Loader/1.0" }
        });
        if (!filesResponse.ok) throw new Error('Failed to fetch MaterialX data');
        
        const filesData = await filesResponse.json();
        const mtlxFiles = filesData.mtlx?.[resolution].mtlx;
        
        if (!mtlxFiles) {
            throw new Error(`No MaterialX files found for ${resolution} resolution`);
        }
        console.log('MaterialX files data:', mtlxFiles);
        
        // Create ZIP file
        const zip = new JSZip();
        
        // 1. Download and add the main MaterialX file
        const mtlxResponse = await fetch(mtlxFiles.url, {
            headers: { "User-Agent": "MTLX_Polyhaven_Loader/1.0" }
        });
        if (!mtlxResponse.ok) throw new Error('Failed to download MaterialX file');
        
        const mtlxContent = await mtlxResponse.text();
        zip.file(`${materialId}.mtlx`, mtlxContent);
        
        // 2. Download and add all included texture files
        const textureFiles = mtlxFiles.include || {};
        const texturePromises = Object.entries(textureFiles).map(async ([path, fileData]) => {
            try {
                const textureResponse = await fetch(fileData.url, {
                    headers: { "User-Agent": "MTLX_Polyhaven_Loader/1.0" }
                });
                if (!textureResponse.ok) throw new Error(`Failed to download ${path}`);
                
                const textureBlob = await textureResponse.blob();
                zip.file(path, textureBlob);
                
                if (path.toLowerCase().endsWith('.exr')) {
                    console.warn(`EXR file present which may not be supported by MaterialX texture loader: ${path}`);
                }
            } catch (error) {
                console.error(`Error downloading texture ${path}:`, error);
                // Add placeholder file if download fails
                zip.file(path, `Failed to download: ${fileData.url}`);
            }
        });
        
        // 3. Download and add thumbnail
        if (currentSelectedMaterial.thumb_url) {
            try {
                const thumbResponse = await fetch(currentSelectedMaterial.thumb_url, {
                    headers: { "User-Agent": "MTLX_Polyhaven_Loader/1.0" }
                });
                if (thumbResponse.ok) {
                    const thumbBlob = await thumbResponse.blob();
                    const thumbExt = currentSelectedMaterial.thumb_url.split('.').pop().split('?')[0];
                    zip.file(`${materialId}_thumbnail.${thumbExt}`, thumbBlob);
                }
            } catch (error) {
                console.error('Error downloading thumbnail:', error);
            }
        }
        
        // Wait for all downloads to complete
        await Promise.all(texturePromises);
        
        // Generate the ZIP file
        const content = await zip.generateAsync({ type: 'blob' });
        
        // Trigger download
        const url = URL.createObjectURL(content);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${materialName}_${resolution}_materialx.zip`;
        document.body.appendChild(a);
        a.click();
        
        // Clean up
        setTimeout(() => {
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }, 100);
        
    } catch (error) {
        console.error('Error creating MaterialX package:', error);
        alert(`Failed to prepare download: ${error.message}`);
    } finally {
        // Restore button state
        downloadBtn.innerHTML = originalText;
        downloadBtn.disabled = false;
    }
}

// Load materials from Poly Haven API
async function loadMaterials() {
    mainSpinner.style.display = 'block';
    materialsContainer.innerHTML = '';
    
    try {
        // Fetch all textures from Poly Haven API
        const response = await fetch('https://api.polyhaven.com/assets?t=textures');
        const data = await response.json();
        
        // Process the data
        allMaterials = [];
        categories = new Set();
        
        for (const [id, materialData] of Object.entries(data)) {
            // Skip materials without required data
            if (!materialData.name || !materialData.categories) continue;
            
            // Add material to our list
            const material = {
                id,
                name: materialData.name,
                description: materialData.description || 'No description available',
                categories: materialData.categories,
                tags: materialData.tags || [],
                thumb_url: `https://cdn.polyhaven.com/asset_img/thumbs/${id}.png?width=512`,
                maps: materialData.maps || {}
            };
            
            allMaterials.push(material);
            
            // Add categories to our set
            material.categories.forEach(cat => categories.add(cat));
        }
        
        // Populate category filter
        populateCategoryFilter();
        
        // Display all materials initially
        filterMaterials();
    } catch (error) {
        console.error('Error loading materials:', error);
        materialsContainer.innerHTML = `
            <div class="col-12">
                <div class="alert alert-danger" role="alert">
                    Failed to load materials from Poly Haven. Please try again later.
                </div>
            </div>
        `;
    } finally {
        mainSpinner.style.display = 'none';
    }
}

// Populate the category filter dropdown
function populateCategoryFilter() {
    categoryFilter.innerHTML = '<option value="">All Categories</option>';
    
    const sortedCategories = Array.from(categories).sort();
    sortedCategories.forEach(category => {
        const option = document.createElement('option');
        option.value = category;
        option.textContent = category.charAt(0).toUpperCase() + category.slice(1);
        categoryFilter.appendChild(option);
    });
}

// Filter materials based on search and category filters
function filterMaterials() {
    const searchTerm = searchInput.value.toLowerCase();
    const selectedCategory = categoryFilter.value;
    
    const filtered = allMaterials.filter(material => {
        // Filter by search term
        const matchesSearch = material.name.toLowerCase().includes(searchTerm) || 
                             material.description.toLowerCase().includes(searchTerm) ||
                             material.tags.some(tag => tag.toLowerCase().includes(searchTerm));
        
        // Filter by category
        const matchesCategory = !selectedCategory || material.categories.includes(selectedCategory);
        
        return matchesSearch && matchesCategory;
    });
    
    displayMaterials(filtered);
}

// Display materials in the grid
function displayMaterials(materials) {
    materialsContainer.innerHTML = '';
    
    if (materials.length === 0) {
        materialsContainer.innerHTML = `
            <div class="col-12">
                <div class="alert alert-info" role="alert">
                    No materials found matching your criteria.
                </div>
            </div>
        `;
        return;
    }
    
    materials.forEach(material => {
        const col = document.createElement('div');
        col.className = 'col-md-4 col-lg-3 mb-4';
        
        col.innerHTML = `
            <div class="card material-card" data-material-id="${material.id}">
                <img src="${material.thumb_url}" class="card-img-top material-img" alt="${material.name}" onerror="this.src='https://via.placeholder.com/512?text=No+Preview'">
                <div class="card-body">
                    <h5 class="card-title">${material.name}</h5>
                    <div class="d-flex flex-wrap">
                        ${material.categories.map(cat => `<span class="badge bg-secondary category-badge">${cat}</span>`).join('')}
                    </div>
                </div>
            </div>
        `;
        
        col.querySelector('.card').addEventListener('click', () => showMaterialDetails(material));
        materialsContainer.appendChild(col);
    });
}

// Show material details in modal
function showMaterialDetails(material) {
    currentSelectedMaterial = material;
    
    // Set basic info
    document.getElementById('materialModalLabel').textContent = material.name;
    document.getElementById('materialTitle').textContent = material.name;
    document.getElementById('materialDescription').textContent = material.description;
    document.getElementById('materialPreview').src = material.thumb_url;
    
    // Set tags
    const tagsContainer = document.getElementById('materialTags');
    tagsContainer.innerHTML = material.tags.map(tag => `<span class="badge bg-light text-dark">${tag}</span>`).join(' ');
    
    // Update maps display
    updateMapsDisplay();
    
    // Show modal
    materialModal.show();
}

// Update the maps display based on selected resolution
function updateMapsDisplay() {
    if (!currentSelectedMaterial) return;
    
    const resolution = document.getElementById('materialResolution').value;
    const mapsContainer = document.getElementById('materialMaps');
    mapsContainer.innerHTML = '';
    
    for (const [mapType, available] of Object.entries(currentSelectedMaterial.maps)) {
        if (available) {
            const badge = document.createElement('span');
            badge.className = 'badge bg-info text-dark map-badge';
            badge.textContent = `${mapType} (${resolution})`;
            mapsContainer.appendChild(badge);
        }
    }
}

// Download material handler
function downloadMaterial2() {
    if (!currentSelectedMaterial) return;
    
    const resolution = document.getElementById('materialResolution').value;
    const materialId = currentSelectedMaterial.id;
    
    // In a real implementation, this would trigger downloads of each map
    alert(`Downloading ${currentSelectedMaterial.name} at ${resolution} resolution.\n\nThis would normally download all available maps.`);
    
    // Example download URLs (would need proper implementation)
    console.log(`Example download URLs for ${materialId} at ${resolution}:`);
    for (const [mapType, available] of Object.entries(currentSelectedMaterial.maps)) {
        if (available) {
            console.log(`https://cdn.polyhaven.com/asset_img/textures/${materialId}/${mapType}_${resolution}.png`);
        }
    }
}

// Copy material link handler
function copyMaterialLink() {
    if (!currentSelectedMaterial) return;
    
    const materialUrl = `https://polyhaven.com/a/${currentSelectedMaterial.id}`;
    navigator.clipboard.writeText(materialUrl)
        .then(() => {
            const button = document.getElementById('copyMaterialLink');
            const originalText = button.innerHTML;
            button.innerHTML = '<i class="fas fa-check me-2"></i>Copied!';
            setTimeout(() => {
                button.innerHTML = originalText;
            }, 2000);
        })
        .catch(err => {
            console.error('Failed to copy link: ', err);
            alert('Failed to copy link to clipboard');
        });
}