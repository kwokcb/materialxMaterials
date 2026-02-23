// Global variables
let allMaterials = [];
let categories = new Set();
let currentSelectedMaterial = null;
let polyHavenAPI = null;
let svgDataUrl = null;
let codeMirrorEditor = null;
const materialPackageCache = {};
const materialContentCache = {};

// DOM elements
const materialsContainer = document.getElementById('materialsContainer');
const searchInput = document.getElementById('searchInput');
const searchButton = document.getElementById('searchButton');
const categoryFilter = document.getElementById('categoryFilter');
const resolutionFilter = document.getElementById('resolutionFilter');
const mainSpinner = document.getElementById('mainSpinner');
const materialModal = new bootstrap.Modal(document.getElementById('materialModal'));

// Target URL for the viewer page
let targetURL = "https://kwokcb.github.io/MaterialXLab/javascript/shader_utilities/dist/index.html?viewerOnly=1";
// Set for local testing
//targetURL = "http://localhost:8010/javascript/shader_utilities/dist/index.html?viewerOnly=1";

 function setTheme(mode) {
    document.documentElement.setAttribute('data-bs-theme', mode);
    document.getElementById('themeIcon').className = mode === 'dark' ? 'bi bi-sun' : 'bi bi-moon';
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function () {
    // Initialize the Poly Haven API
    polyHavenAPI = new JsPolyHavenAPILoader();

    // Set theme based on browser preference or default to light mode
    const prefersDarkScheme = window.matchMedia("(prefers-color-scheme: dark)").matches;
    if (prefersDarkScheme) {
        setTheme('dark');
    } else {
        setTheme('light');
    }

    document.getElementById('themeToggleBtn').addEventListener('click', function () {
        const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
        setTheme(isDark ? 'light' : 'dark');
    });    

    // https://icons.getbootstrap.com/icons/card-image/    
    const svgString = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-card-image" viewBox="0 0 16 16">
    <path d="M6.002 5.5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0"/>
    <path d="M1.5 2A1.5 1.5 0 0 0 0 3.5v9A1.5 1.5 0 0 0 1.5 14h13a1.5 1.5 0 0 0 1.5-1.5v-9A1.5 1.5 0 0 0 14.5 2zm13 1a.5.5 0 0 1 .5.5v6l-3.775-1.947a.5.5 0 0 0-.577.093l-3.71 3.71-2.66-1.772a.5.5 0 0 0-.63.062L1.002 12v.54L1 12.5v-9a.5.5 0 0 1 .5-.5z"/>
    </svg>`;

    // Convert to base64 data URL
    // svgDataUrl = `data:image/svg+xml;base64,${btoa(svgString)}`;''
    svgDataUrl = 'https://icons.getbootstrap.com/assets/icons/card-image.svg'


    loadMaterials();

    // Event listeners
    searchButton.addEventListener('click', filterMaterials);
    searchInput.addEventListener('keyup', function (e) {
        if (e.key === 'Enter') filterMaterials();
    });
    categoryFilter.addEventListener('change', filterMaterials);
    resolutionFilter.addEventListener('change', filterMaterials);

    // Modal buttons
    document.getElementById('downloadMaterial').addEventListener('click', downloadMaterial);
    document.getElementById('copyMaterialLink').addEventListener('click', copyMaterialLink);
    document.getElementById('materialResolution').addEventListener('change', updateMapsDisplay);
    document.getElementById('previewMaterial').addEventListener('click', previewMaterial);

    // Initialize CodeMirror when modal opens
    const materialModalElement = document.getElementById('materialModal');
    materialModalElement.addEventListener('shown.bs.modal', function () {
        if (codeMirrorEditor) 
        {
            // Clear content
            codeMirrorEditor.setValue('');
            return;
        }

        let editor = document.getElementById('mtlxEditor')
        if (editor)
            codeMirrorEditor = CodeMirror.fromTextArea(editor, {
                mode: 'xml',
                theme: 'material',
                lineNumbers: true,
                readOnly: true,
                lineWrapping: true
            });

        let textureGallery = document.getElementById('textureGallery');
        if (textureGallery) {
            // clear
            console.info('Texture gallery container cleared !!!!!!!!');
            textureGallery.innerHTML = '';
        }
        else {
            console.info('Texture gallery container not found !!!!!!!!');
        }
    });

    let viewer = document.getElementById('viewer');
    viewer.src = targetURL;

    materialModalElement.addEventListener('hidden.bs.modal', function () {
        if (viewer) {
            viewer.style.display = 'none';
        }

        // Clear the cache when the modal closes
        for (const key in materialPackageCache) {
            delete materialPackageCache[key];
        }        

        let contentPreview = document.getElementById('contentPreview');
        if (contentPreview) {
            contentPreview.style.display = 'none';
        }   
    });
});

async function downloadMaterial() {
    if (!currentSelectedMaterial || !polyHavenAPI) return;

    console.log(`Preparing download for material: ${currentSelectedMaterial.name} (ID: ${currentSelectedMaterial.id})`);

    const resolution = document.getElementById('materialResolution').value;
    const materialName = currentSelectedMaterial.name.replace(/[^a-z0-9]/gi, '_').toLowerCase();

    // Show loading state
    const downloadBtn = document.getElementById('downloadMaterial');
    const originalText = downloadBtn.innerHTML;
    downloadBtn.innerHTML = '<i class="bi bi-arrow-clockwise spin me-2"></i>Preparing download...';
    downloadBtn.disabled = true;

    try {
        const cacheKey = `${currentSelectedMaterial.id}_${resolution}`;
        let zipBlob = materialPackageCache[cacheKey];
        if (!zipBlob) {
            zipBlob = await polyHavenAPI.createMaterialXPackage(currentSelectedMaterial, resolution);
            materialPackageCache[cacheKey] = zipBlob;
        }

        // Create the MaterialX package using the API class
        //const zipBlob = await polyHavenAPI.createMaterialXPackage(currentSelectedMaterial, resolution);

        // Trigger download
        const url = URL.createObjectURL(zipBlob);
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

function waitForViewerReady(viewer) {
    return new Promise((resolve) => {
        function handler(event) {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'viewer-ready') {
                    window.removeEventListener('message', handler);
                    resolve();
                }
            } catch (e) {
                // Ignore non-JSON messages
            }
        }
        window.addEventListener('message', handler);
    });
}

async function previewMaterial() {
    if (!currentSelectedMaterial || !polyHavenAPI) return;

    let viewer = document.getElementById('viewer');
    if (!viewer) {
        console.info('Viewer not found !');
    }

    let previewButton = document.getElementById('previewMaterial')
    let previousHTML = previewButton.innerHTML;
    previewButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Loading...';

    const resolution = document.getElementById('materialResolution').value;
    try {
        const cacheKey = `${currentSelectedMaterial.id}_${resolution}`;
        let zipBlob = materialPackageCache[cacheKey];
        if (!zipBlob) {
            // Reuse cached content if available
            let contentData = materialContentCache[cacheKey];
            if (!contentData) {
                contentData = await polyHavenAPI.getMaterialContent(currentSelectedMaterial.id, resolution);
                materialContentCache[cacheKey] = contentData;
            }
            zipBlob = await polyHavenAPI.createMaterialXPackage(currentSelectedMaterial, resolution);
            materialPackageCache[cacheKey] = zipBlob;
        }

        // Convert Blob to ArrayBuffer
        const arrayBuffer = await zipBlob.arrayBuffer();

        // Show viewer immediately, before posting message
        viewer.style.display = 'block';

        // Post the ArrayBuffer to the target window (e.g., iframe or parent)
        console.log('Posting preview data to viewer page...');
        if (viewer && viewer.contentWindow) {
            viewer.contentWindow.postMessage(arrayBuffer, targetURL);
        }

        // Wait for viewer-ready message after posting
        await waitForViewerReady(viewer);

    } catch (error) {
        console.error('Error preparing preview:', error);
        alert(`Failed to prepare preview: ${error.message}`);
    } finally {
        previewButton.innerHTML = previousHTML;
    }

}


// Load materials from Poly Haven API
async function loadMaterials() {
    if (!polyHavenAPI) {
        console.error('PolyHaven API not initialized');
        return;
    }

    mainSpinner.style.display = 'block';
    materialsContainer.innerHTML = '';

    try {
        // Fetch materials using the API class
        const result = await polyHavenAPI.fetchMaterials();
        
        allMaterials = result.materials;
        categories = result.categories;

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
        col.className = 'col-md-3 col-lg-2 mb-4';

        col.innerHTML = `
            <div class="card material-card" data-material-id="${material.id}">
                <img src="${material.thumb_url}" class="card-img-top material-img" alt="${material.name}" loading="lazy" decoding="async" onerror="this.src=${svgDataUrl}">
                <div class="card-body">
                    <div class="card-title">${material.name}</div>
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

// New function to load material content
async function loadMaterialContent(materialId) {
    if (!polyHavenAPI) {
        console.error('PolyHaven API not initialized');
        return;
    }

    // Show content preview section
    let contentPreview = document.getElementById('contentPreview');
    contentPreview.style.display = 'block';

    const loadBtn = document.getElementById('loadContentBtn');
    const originalText = loadBtn.innerHTML;
    loadBtn.innerHTML = '<i class="bi bi-arrow-clockwise spin me-2"></i>Loading...';
    loadBtn.disabled = true;

    //const previewContainer = document.getElementById('contentPreview');

    const resolution = document.getElementById('materialResolution').value;
    const cacheKey = `${materialId}_${resolution}`;
    let contentData = materialContentCache[cacheKey];

    try {
        if (!contentData) 
        {
            contentData = await polyHavenAPI.getMaterialContent(materialId, resolution);
            materialContentCache[cacheKey] = contentData;
        }
        
        // Create preview content
        let mtlxContent = contentData.mtlxContent || '';

        // Load texture gallery
        const textureFiles = contentData.textureFiles;
        const galleryContainer = document.getElementById('textureGallery');
        galleryContainer.innerHTML = '';
        
        let textureNames = [];

        const createTextureCard = (textureName, textureUrl) => 
        {
            const card = document.createElement('div');
            card.className = 'col-sm-3 col-md-3 col-lg-3 mb-2';

            // If textureURL ends with exr replace with png for preview
            if (textureUrl.toLowerCase().endsWith('.exr')) {
                console.log(`> EXR file detected for preview, attempting to use PNG version: ${textureUrl}`);
                textureUrl = textureUrl.replace(/\.exr$/i, '.png').replace(/\/exr\//i, '/png/');
                let textureName_before = textureName;
                textureName = textureName_before.replace(/\.exr$/i, '.png');
                console.log(`Replace ${textureName_before} with ${textureName} in MaterialX content for preview`);
                mtlxContent = mtlxContent.replace(textureName_before, textureName);
            }   

            textureNames.push(textureName);

            card.innerHTML = `
                    <div class="card h-100">
                        <div class="ratio ratio-1x1">
                            <img src="${textureUrl}" 
                                class="card-img-top object-fit-contain p-2"
                                alt="${textureName}"
                                loading="lazy"
                                onerror="this.onerror=null;this.src='${svgDataUrl}';">
                        </div>
                        <div class="card-body p-2">
                            <small class="text-truncate d-block">${textureName}</small>
                        </div>
                    </div>
                `;
            return card;
        };

        // Create gallery items
        for (const [path, fileData] of Object.entries(textureFiles)) {
            const textureURI = path.split('/').pop();
            let card = createTextureCard(textureURI, fileData.url);
            galleryContainer.appendChild(card);
        }

        // Set mtlxContent to editor
        if (codeMirrorEditor) {
            // Patch bad MTLX references in original file
            for (const textureName of textureNames) {
                extenson = textureName.split('.').pop();
                exrName = textureName.replace(`.${extenson}`, `.exr`);
                if (mtlxContent.includes(exrName)) {
                    console.log(`Replace ${exrName} with ${textureName} in MaterialX content for preview`);
                    mtlxContent = mtlxContent.replace(exrName, textureName);
                }
            }

            //console.log('Setting MaterialX content in CodeMirror editor:', mtlxContent);
            codeMirrorEditor.setValue(mtlxContent);
        }

        loadBtn.innerHTML = originalText;
        loadBtn.disabled = false;
    
    } catch (error) {
        console.error('Error loading content:', error);
        previewContainer.innerHTML += `
            <div class="alert alert-danger mt-3">
                Failed to load content: ${error.message}
            </div>
        `;
        loadBtn.innerHTML = originalText;
        loadBtn.disabled = false;
        return;
    }
}

// Modified showMaterialDetails function
async function showMaterialDetails(material) {
    currentSelectedMaterial = material;

    if (codeMirrorEditor) 
    {        
        codeMirrorEditor.setValue(''); 
    }

    // Set basic info
    document.getElementById('materialModalLabel').textContent = material.name;
    //document.getElementById('materialTitle').textContent = material.name;
    document.getElementById('materialDescription').textContent = material.description;
    document.getElementById('materialPreview').src = material.thumb_url;

    // Set tags
    const tagsContainer = document.getElementById('materialTags');
    tagsList = material.tags.map(tag =>
        `<span class="badge bg-secondary">${tag}</span>`
    ).join(' ');
    tagsContainer.innerHTML = '<span class="badge bg-dark">Tags</span> ' + tagsList

    // Set categories
    const categoriesContainer = document.getElementById('materialCategories');
    categoriesList = material.categories.map(cat =>
        `<span class="badge bg-secondary">${cat}</span>`
    ).join(' ');
    categoriesContainer.innerHTML = '<span class="badge bg-dark">Categories</span> ' + categoriesList


    // Set up content loader button
    document.getElementById('loadContentBtn').addEventListener('click', async () => {
        await loadMaterialContent(material.id);
    });

    // Force 1K for downloads
    document.getElementById('materialResolution').value = '1k';

    // Clear texture gallery and editor content
    const galleryContainer = document.getElementById('textureGallery');
    if (galleryContainer) {
        galleryContainer.innerHTML = '';
    }
    if (codeMirrorEditor) {
        codeMirrorEditor.setValue('');
    }

    // Show modal
    materialModal.show();
}

// Update the maps display based on selected resolution
function updateMapsDisplay() {
    return;
    if (!currentSelectedMaterial) return;

    const resolution = document.getElementById('materialResolution').value;
    const mapsContainer = document.getElementById('materialMaps');
    mapsContainer.innerHTML = currentSelectedMaterial.maps;

    /* for (const [mapType, available] of Object.entries(currentSelectedMaterial.maps)) {
        if (available) {
            const badge = document.createElement('span');
            badge.className = 'badge bg-info text-dark map-badge';
            badge.textContent = `${mapType} (${resolution})`;
            mapsContainer.appendChild(badge);
        }
    } */
}

// Copy material link handler
function copyMaterialLink() {
    if (!currentSelectedMaterial) return;

    const materialUrl = `https://polyhaven.com/a/${currentSelectedMaterial.id}`;
    navigator.clipboard.writeText(materialUrl)
        .then(() => {
            const button = document.getElementById('copyMaterialLink');
            const originalText = button.innerHTML;
            button.innerHTML = '<i class="bi bi-check-lg me-2"></i>Copied!';
            setTimeout(() => {
                button.innerHTML = originalText;
            }, 2000);
        })
        .catch(err => {
            console.error('Failed to copy link: ', err);
            alert('Failed to copy link to clipboard');
        });
}