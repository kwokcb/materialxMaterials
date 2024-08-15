<!--Start-->

<h2 class="bg-gradient rounded-2 p-0"> <img src="https://kwokcb.github.io/materialxMaterials/documents/icons/logo_large_blue_teapot_no_text.png" width=32px>MaterialX Materials</h2>

<div class="container p-2 rounded-4 border border-secondary border-rounded">

<h3>Introduction</h3>

Welcome to MaterialX Materials.

This site hosts a set of libraries and command line utilities to
query remote databases for MaterialX materials.

> Visit the <b><a href="https://kwokcb.github.io/materialxMaterials" target="_blank">Home Page</a></b>
<p></p>

The current utilities support:

<div style="display: flex; align-items: center;">
<img src="https://physicallybased.info/images/renders/cycles/600/aluminum.webp" width="64px" style="margin-right: 10px;">
<a href="https://physicallybased.info/">PhysicallyBased database</a> Material descriptions can be downloaded with additional utilities to create materials using either: Autodesk Standard Surface, OpenPBR, or glTF PBR shading model shaders.
</div>
<br>
<div style="display: flex; align-items: center;">
<img src="https://image.matlib.gpuopen.com/afff0c66-dba8-4d79-b96b-459fbd9cbef5.jpeg" width="64px" style="margin-right: 10px;">
<a href="https://matlib.gpuopen.com/main/materials/all">AMD GPUOpen database</a> MaterialX packages can be downloaded (as zip files). Images and MaterialX
documents can be extracted for any of the posted materials in the database.
</div>

Each currently has Python implementations.

A Javascript implementation for extracting <code>PhysicallyBased</code> materials is <a href="https://kwokcb.github.io/MaterialXLab/javascript/PhysicallyBasedMaterialX_out.html" target="_blank">available here.

<img src="https://kwokcb.github.io/materialxMaterials/documents/images/PhysicallBased_Carrot.png" width=100%>
</a>

<h3>Usage</h3>

<h4>Commands</h4>

1. Query all materials fom PhysicallyBased and convert them to all support shading models. Save the material list and corresponding MaterialX files in the default output location. The build will include this information Python package under the <code>data</code> folder.
```sh
python physicallyBasedMaterialX.py
```

2. Query all materials fom GPUOpen. Extract out a few material
packages (zip). Save the material lists, material names and unzipped packages (MaterialX and images) in the default output location.
The build will include this information Python package under the <code>data</code> folder.
```sh
python .GPUOpenLoaderCmd.py --materialNames=1 --saveMaterials=1 
```

<h3>Library</h3>

- Forth-coming...

<h3>Results</h3>

The following are some samples which have been rendered using the `MaterialXView` utility which is part of the MaterialX binary distribution.

<table class="container-flex">
<th>
<tr class="row">
<td class="col">
Emerald Peaks Wallpaper
<td class="col">
Indigo Palm Wallpaper
<td class="col">
Oliana Blue Painted Wood
</th>
<tr class="row">
<td class="col">
<img src="https://kwokcb.github.io/materialxMaterials/src/materialxMaterials/data/GPUOpenMaterialX/Emerald Peaks Wallpaper/Emerald_Peaks_Wallpaper.png" width=100%>
</td>
<td class="col">
<img src="https://kwokcb.github.io/materialxMaterials/src/materialxMaterials/data/GPUOpenMaterialX/Indigo Palm Wallpaper/Indigo_Palm_Wallpaper.png" width=100%>
</td>
<td class="col">
<img src="https://kwokcb.github.io/materialxMaterials/src/materialxMaterials/data/GPUOpenMaterialX/Oliana Blue Painted Wood/Oliana_Blue_Painted_Wood.png" width=100%>
</td>
</tr>
</table>

<table>
<th>
<tr class="row">
<td class="col">
Ketchup
<td class="col">
Cooking Oil
<td class="col">
Brass
</th>
<tr class="row">
<td class="col">
<img src="https://kwokcb.github.io/materialxMaterials/src/materialxMaterials/data/PhysicallyBasedMaterialX/Ketchup.png" width=100%>
</td>
<td class="col">
<img src="https://kwokcb.github.io/materialxMaterials/src/materialxMaterials/data/PhysicallyBasedMaterialX/Cooking_Oil.png" width=100%>
</td>
<td class="col">
<img src="https://kwokcb.github.io/materialxMaterials/src/materialxMaterials/data/PhysicallyBasedMaterialX/Brass.png" width=100%>
</td>
</table>


<h3>Dependencies</h3>

The Python utilities require:

1. The MaterialX 1.39 or greater package for PhysicallyBased OpenPBR shader creation
2. The `requests` package.

<h3>Building</h3>

The <a href="https://github.com/kwokcb/materialxMaterials"><img src="https://raw.githubusercontent.com/kwokcb/materialxMaterials/20cbe6bde0844699824a9a7a05afe882c42b071d/documents/icons/github-mark-white.svg?token=ALYVGHLEDNQAPHZHPUNJNP3GXTAUQ" width=16px> GitHub repository</a> can be cloned and the package built using:

```
pip install .
```

This will pull down the dependent packages as needed.

<h3>API Reference</h3>

The API reference can be found <a href="https://kwokcb.github.io/materialxMaterials/documents/html/index.html">here</a>

</div>
<!--End-->

