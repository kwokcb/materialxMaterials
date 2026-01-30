// Global variables
let allMaterials = [];
let categories = new Set();
let currentSelectedMaterial = null;
let polyHavenAPI = null;
let svgDataUrl = null;
let codeMirrorEditor = null;

// DOM elements
const materialsContainer = document.getElementById('materialsContainer');
const searchInput = document.getElementById('searchInput');
const searchButton = document.getElementById('searchButton');
const categoryFilter = document.getElementById('categoryFilter');
const resolutionFilter = document.getElementById('resolutionFilter');
const mainSpinner = document.getElementById('mainSpinner');
const materialModal = new bootstrap.Modal(document.getElementById('materialModal'));


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

    // Initialize CodeMirror when modal opens
    const materialModalElement = document.getElementById('materialModal');
    materialModalElement.addEventListener('shown.bs.modal', function () {
        if (codeMirrorEditor) return;

        let editor = document.getElementById('mtlxEditor')
        if (editor)
            codeMirrorEditor = CodeMirror.fromTextArea(editor, {
                mode: 'xml',
                theme: 'material',
                lineNumbers: true,
                readOnly: true,
                lineWrapping: true
            });
    });
});

async function downloadMaterial() {
    if (!currentSelectedMaterial || !polyHavenAPI) return;

    const resolution = document.getElementById('materialResolution').value;
    const materialName = currentSelectedMaterial.name.replace(/[^a-z0-9]/gi, '_').toLowerCase();

    // Show loading state
    const downloadBtn = document.getElementById('downloadMaterial');
    const originalText = downloadBtn.innerHTML;
    downloadBtn.innerHTML = '<i class="bi bi-arrow-clockwise spin me-2"></i>Preparing download...';
    downloadBtn.disabled = true;

    try {
        // Create the MaterialX package using the API class
        const zipBlob = await polyHavenAPI.createMaterialXPackage(currentSelectedMaterial, resolution);

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
        col.className = 'col-md-4 col-lg-3 mb-4';

        col.innerHTML = `
            <div class="card material-card" data-material-id="${material.id}">
                <img src="${material.thumb_url}" class="card-img-top material-img" alt="${material.name}" onerror="this.src=${svgDataUrl}">
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

// New function to load material content
async function loadMaterialContent(materialId) {
    if (!polyHavenAPI) {
        console.error('PolyHaven API not initialized');
        return;
    }

    const loadBtn = document.getElementById('loadContentBtn');
    const originalText = loadBtn.innerHTML;
    loadBtn.innerHTML = '<i class="bi bi-arrow-clockwise spin me-2"></i>Loading...';
    loadBtn.disabled = true;

    try {
        const resolution = document.getElementById('materialResolution').value;
        
        // Get material content using the API class
        const contentData = await polyHavenAPI.getMaterialContent(materialId, resolution);

        // Create preview content
        const previewContainer = document.getElementById('contentPreview');
        previewContainer.innerHTML = `
            <div class="mt-4">
                <h5>MaterialX Document</h5>
                <textarea id="mtlxEditor">${contentData.mtlxContent}</textarea>
                <div class="mt-4">
                    <h5>Textures</h5>
                    <div id="textureGallery" class="row g-2"></div>
                </div>
            </div>
        `;

        // Initialize CodeMirror
        if (codeMirrorEditor) {
            codeMirrorEditor.toTextArea();
        } 
        let editor = document.getElementById('mtlxEditor');
        if (editor) {
            codeMirrorEditor = CodeMirror.fromTextArea(editor, {
                mode: 'xml',
                theme: 'material',
                lineNumbers: true,
                readOnly: true,
                lineWrapping: true
            });
        }

        // Load texture gallery
        const textureFiles = contentData.textureFiles;
        const galleryContainer = document.getElementById('textureGallery');
        galleryContainer.innerHTML = '';

        const createTextureCard = (textureName, textureUrl) => {
            const card = document.createElement('div');
            card.className = 'col-6 col-md-4 col-lg-3 mb-3';

            card.innerHTML = `
                    <div class="card h-100">
                        <div class="ratio ratio-1x1 bg-light">
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
            const textureName = path.split('/').pop();
            const card = createTextureCard(textureName, fileData.url);
            galleryContainer.appendChild(card);
        }

    } catch (error) {
        console.error('Error loading content:', error);
        document.getElementById('contentPreview').innerHTML += `
            <div class="alert alert-danger mt-3">
                Failed to load content: ${error.message}
            </div>
        `;
    } finally {
        loadBtn.innerHTML = originalText;
        loadBtn.disabled = false;
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
    document.getElementById('materialTitle').textContent = material.name;
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
    categoriesContainer.innerHTML = '<span class="badge bg-dark">Cartegories</span> ' + categoriesList

    // Reset content preview section
    document.getElementById('contentPreview').innerHTML = `
        <div class="text-center py-4">
            <button class="btn btn-primary" id="loadContentBtn">
                <i class="bi bi-eye me-2"></i>Show Content
            </button>
        </div>
    `;

    // Set up content loader button
    document.getElementById('loadContentBtn').addEventListener('click', async () => {
        await loadMaterialContent(material.id);
    });

    // Force 1K for downloads
    document.getElementById('materialResolution').value = '1k';

    // Show modal
    materialModal.show();
}

// Update the maps display based on selected resolution
function updateMapsDisplay() {
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