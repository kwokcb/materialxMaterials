## Supported MaterialX Sites

This repository supports downloading assets from several sites using both JavaScript (JS) and Python tools. Below is a summary of the supported sites, download formats, and related details. 

<super>Note that `PhysicallyBased` is not included here as there are no referenced assets and MaterialX content
is generated from the native material descriptions.</super>

#### Root Document Format Support

| Site        | MaterialX (.mtlx) | Blender (.blend) | USD (.usd/.usdz) | Notes |
|-------------|------------------|------------------|------------------|-------|
| Poly Haven  | Yes              | Yes              | Yes              | Multiple formats available per asset. Loader here only fetches MaterialX (`mtlx`). |
| AmbientCG   | Yes              | Yes              | No               | Zips may contain MaterialX, Blender, and other formats with resource reuse |
| GPUOpen     | Yes              | No               | No               | Only MaterialX (`.mtlx`) and textures are provided. |

This repository only deals with MaterialX root documents, though could be extended to extract
other information as additional fetches or from downloaded zip content.

* **Poly Haven**: The API provides multiple root document types (MaterialX, Blender, USD, etc.), but the loader in this repo is focused on MaterialX (`mtlx`). Other formats are available via the API.
* **AmbientCG**: Zips may contain MaterialX, Blender, and other formats, but the loader here typically extracts MaterialX.
* **GPUOpen**: Only MaterialX (`.mtlx`) and textures are available.



### Sites

#### 1. Poly Haven (includes Texture Haven)
- **Python & JS**: Each MaterialX asset and its textures are fetched as separate files (not as a single zip from the server).
- **Number of Fetches**: Multiple HTTP fetches per asset: one for the MaterialX file, one for each texture, and one for the thumbnail.
- **Zipping**: The loader creates a zip locally containing the `.mtlx` and all textures for convenience. Extraction is optional.

#### 2. AmbientCG
- **Python & JS**: Each material is provided as a single zip file directly from the provider.
- **Number of Fetches**: One fetch per material (the zip file).
- **Zipping**: Not required, as assets are already zipped by the provider. Extraction is optional.

#### 3. GPUOpen
- **Python & JS**: Each material package is fetched as a single zip file from the server.
- **Number of Fetches**: One fetch per package (zip file).
- **Zipping**: The zip is extracted after download to access the `.mtlx` and texture files.

### Creating Zip Archives from Separate Assets
- **Python**: zipfile can be used
```
import zipfile
with zipfile.ZipFile('archive.zip', 'w') as zipf:
    zipf.write('file1.png')
    zipf.write('file2.hdr')
```
- **JavaScript**: Use the [`jszip`](https://stuk.github.io/jszip/) library to create zips in-browser or Node.js.

#### Resolution Support for Referenced Images

| Site        | Resolution Variants Supported | How It Works |
|-------------|------------------------------|--------------|
| Poly Haven  | Yes (1k, 2k, 4k, 8k)         | The loader fetches MaterialX and textures for the selected resolution. Multiple resolutions are available per asset. |
| AmbientCG   | Yes (1k, 2k, 4k, 8k)         | The loader does not select or expose different resolutions for referenced images. Zips may contain only one resolution. |
| GPUOpen     | Yes (package index)          | Multiple packages per material, each with a different texture resolution. Index 0 is the smallest. The loader fetches the package for the selected resolution. |

### Summary

| Site        | Download Format                | Fetches per Asset | Extraction Needed? | Local Zipping? |
|-------------|-------------------------------|-------------------|--------------------|---------------|
| Poly Haven  | Separate files, zipped locally | Multiple          | Optional           | Yes           |
| AmbientCG   | Single zip from server         | One               | Optional           | No            |
| GPUOpen     | Single zip from server         | One               | Yes                | No            |

---
For more details, see the documentation or code examples in the repo.
