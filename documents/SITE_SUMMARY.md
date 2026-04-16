## Supported MaterialX Sites

This repository supports downloading assets from several sites using both JavaScript (JS) and Python tools. Below is a summary of the supported sites, download formats, and related details. 

### Root Document Format Support

This repository only deals with `MaterialX` root documents, though could be extended to extract other information as additional fetches or from downloaded zip content.


| Site        | `MaterialX` (.mtlx) | Blender (.blend) | USD (.usd/.usdz) | Notes |
|-------------|------------------|------------------|------------------|-------|
| `PhysicallyBased` | Custom       | No               |  No              | `MaterialX` is generated from custom `JSON` descriptions. `MaterialX`, Unreal and Unity format support via interactive site |  
| `Poly Haven`  | Yes              | Yes              | Yes              | Multiple formats available per asset. Loader here only fetches `MaterialX` (`mtlx`). |
| `AmbientCG`   | Yes              | Yes              | No               | Zips may contain `MaterialX`, Blender, and other formats with image resource being reused |
| `GPUOpen`      | Yes              | No               | No               | Only `MaterialX` (`.mtlx`) and textures are provided. |


* **Poly Haven**: The API provides multiple root document types (`MaterialX`, Blender, USD, etc.), but the loader in this repo is focused on `MaterialX` (`mtlx`). Other formats are available via the API.
* **AmbientCG**: Zips may contain `MaterialX`, Blender, and other formats, but the loader here typically extracts `MaterialX`.
* **GPUOpen**: Only `MaterialX` (`.mtlx`) and textures are available.

### Sites

#### PhysicallyBased
- **Python & JS** : The custom material list is parsed and can generate any of : Autodesk Standard Surface,
glTF PBR or OpenPBR materials, custom `PhysicallyBased` `MaterialX` node definition (and translator). V1 supported. V2 support in progress.

#### `Poly Haven` 
- **Python & JS**: Each `MaterialX` asset and its textures are fetched as separate files (not as a single zip from the server).
- **Number of Fetches**: Multiple HTTP fetches per asset: one for the `MaterialX` file, one for each texture, and one for the thumbnail.
- **Zipping**: The loader creates a zip locally containing the `.mtlx` and all textures for convenience. Extraction is optional.

#### AmbientCG
- **Python & JS**: Each material is provided as a single zip file directly from the provider.
- **Number of Fetches**: One fetch per material (the zip file).
- **Zipping**: Not required, as assets are already zipped by the provider. Extraction is optional.

#### GPUOpen
- **Python & JS**: Each material package is fetched as a single zip file from the server.
- **Number of Fetches**: One fetch per package (zip file).
- **Zipping**: The zip is extracted after download to access the `.mtlx` and texture files.

### Zip Archive Utilities

The appropriate zip library / package is used to create zips or extract from zips from command line, in-browser or Node.js.

#### Resolution Support for Referenced Images

| Site        | Resolution Variants Supported | How It Works |
|-------------|------------------------------|--------------|
| `PhysicallyBased`  | N/A         | The loader fetches the material list, and parses it to create the desired shading model materials. Colorspaces supported in V2. |
| `Poly Haven`  | Yes (1k, 2k, 4k, 8k)         | The loader fetches `MaterialX` and textures for the selected resolution. Multiple resolutions are available per asset. |
| `AmbientCG`   | Yes (1k, 2k, 4k, 8k)         | The loader fetches `MaterialX` and textures for the selected  resolution and format (codec).  Zips may contain only one resolution. |
| `GPUOpen`      | Yes (package index)          | Multiple packages per material, each with a different texture resolution. Index 0 is the smallest. The loader fetches the package for the selected resolution. |

### Summary

| Site        | Download Format                | Fetches per Asset | Extraction Needed? | Local Zipping? |
|-------------|-------------------------------|-------------------|--------------------|---------------|
| `PhysicallyBased`  | Single `JSON` material list | One for all assets          | N/A           | N/A           |
| `Poly Haven`  | Separate files, zipped locally | Multiple          | Optional           | Yes           |
| `AmbientCG`   | Single zip from server         | One               | Optional           | No            |
| `GPUOpen`      | Single zip from server         | One               | Yes                | No            |

---
For more details, see the documentation and code examples in the repo.
