# %% [markdown]
# ## Using the materialxMaterials API
# 
# To use the API the package can be installed by cloning the repository and then installing it using pip

# %%
# pip install . 

# %% [markdown]
# Each loader is encapsulated in a different class. Currently there are two loaders:
# 
# - `GPUOpenMaterialLoader` which can downlad materials from the AMD GPUOpen database
# - `PhysicallyBasedMaterialXLoader` which can download materials from the PhysicallyBased database

# %% [markdown]
# ### GPUOpenMaterialLoader

# %%
from materialxMaterials import GPUOpenLoader

loader = GPUOpenLoader.GPUOpenMaterialLoader()

# Download materials
materials = loader.getMaterials()
materialNames = loader.getMaterialNames()
materialCount = len(materialNames)
print(f'Available number of materials: {materialCount}')


# %% [markdown]
# #### Downloading Material Packages
# 
# A regular expression can be used to search for materials. The search is case insensitive and the regular expression is applied to the material name.
# 
# The `downloadPackageByExpression()` method is used below to download all materials that contain the word "Canyon Maple Dark Wood" in their name.
# 
# The second argument specifies the package number. Different packages have different resolution images. We use `0` to get the first package.

# %%
searchExpr = 'Canyon Maple Dark Wood'
dataItems = loader.downloadPackageByExpression(searchExpr, 0)
for dataItem in dataItems:
    print('Found material: ', dataItem[1])
    data = dataItem[0]
    title = dataItem[1]

# %% [markdown]
# The `downloadPackageByExpression()` method returns a list of material data. The data is in the form of a zip file from which data can be extracted.
# 
# In the sample code, the MaterialX file and the images are extracted from the zip file. Image extraction requires passing over the `pillow` module.

# %%
import io
import zipfile
from PIL import Image
from IPython.display import display

extracted_data = loader.extractPackageData(data, Image)
if extracted_data:
    for item in extracted_data:
        if item['type'] == 'mtlx':
            print(f'- MaterialX file {item["file_name"]}')
        elif item["type"] == 'image':
            print(f'- Image file {item["file_name"]}')
            image = item["data"]
            display(image)

# %% [markdown]
# Materials packages can also be downloaded by index into the material lists. The `downloadPackageByIndex()` method is used to download the the 3rd material in the list. The last argument is the package number.

# %%
indices = [0, 2, 0]
materialList = int(indices[0])
materialIndex = int(indices[1])
materialPackage = int(indices[2])
[data, title] = loader.downloadPackage(materialList, materialIndex, materialPackage)

extracted_data = loader.extractPackageData(data, None)
if extracted_data:
    for item in extracted_data:
        if item['type'] == 'mtlx':
            print(f'- MaterialX file {item["file_name"]}')
        elif item["type"] == 'image':
            print(f'- Image file {item["file_name"]}')


# %% [markdown]
# ## PhysicallyBasedMaterialXLoader
# 
# The `PhysicallyBasedMaterialXLoader` has a dependence on MaterialX to generate MaterialX documents from the material
# descriptions downloaded from the PhysicallyBased database.
# 
# The material information can first be downloaded using `getMaterialsFromURL()` method. The method returns a list of material data in JSON format

# %%
from materialxMaterials import physicallyBasedMaterialX as pbmx
import MaterialX as mx

jsonMat = None
pb_loader = pbmx.PhysicallyBasedMaterialLoader(mx, None)
jsonMat = pb_loader.getMaterialsFromURL()

# Print JSON formatted
#import json
#print(json.dumps(jsonMat, indent=4))

# %% [markdown]
# This data can be parsed to create MaterialX documents using the `convertToMaterialX()` method.
# 

# %%
shadingModels = ['standard_surface', 'gltf_pbr', 'open_pbr_surface']
shadingModelPrefixes = ['SS', 'GLTF', 'OPBR']
matdoc = pb_loader.convertToMaterialX(['Banana'], shadingModels[0], {}, shadingModelPrefixes[0])
print(pb_loader.convertToMaterialXString())

