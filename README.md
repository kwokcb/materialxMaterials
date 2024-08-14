<h2 class="bg-gradient rounded-2 p-2"> <img src="https://kwokcb.github.io/materialxMaterials/documents/icons/logo_large_blue_teapot_no_text.png" width=32px>MaterialX Materials</h2>

### Introduction

Welcome to MaterialX Materials.

This site hosts a set of libraries and command line utilities to
query remote databases for MaterialX materials.

> Visit the <b><a href="https://kwokcb.github.io/materialxMaterials" target="_blank">Home Page</a>
</b>
<p>

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

A Javascript implementation for extracting <code>PhysicallyBased</code> materials is 
 <a href="https://kwokcb.github.io/MaterialXLab/javascript/PhysicallyBasedMaterialX_out.html" target="_blank">available here.
<img src="https://kwokcb.github.io/materialxMaterials/documents/images/PhysicallBased_Carrot.png" width=100%>
</a>

<p>

<hr>
<h3> Examples</h3>

<h4>Command Line Utilities</h4>

1. Query all materials fom PhysicallyBased and convert them to all support shading models. Save the material list and corresponding MaterialX files in the default output location.
```sh
python physicallyBasedMaterialX.py
```

2. Query all materials fom GPUOpen. Extract out a few material
packages (zip). Save the material lists and unzipped packages (MaterialX and images) in the default output location.
```sh
python GPUOpenLoaderCmd.py.py
```

<h3>API Examples</h3>
- Forth-coming...

<h3>Dependencies</h3>

The Python utilities require:

1. The MaterialX 1.39 or greater package for PhysicallyBased OpenPBR shader creation
2. The `requests` package.

### Building

The <a href="https://github.com/kwokcb/materialxMaterials"><img src="https://raw.githubusercontent.com/kwokcb/materialxMaterials/20cbe6bde0844699824a9a7a05afe882c42b071d/documents/icons/github-mark-white.svg?token=ALYVGHLEDNQAPHZHPUNJNP3GXTAUQ" width=16px> GitHub repository</a> can be cloned and the package built using:

```
pip install .
```
This will pull down the dependent packages as needed.

<h3>API Reference</h3>

The API reference can be found <a href="https://kwokcb.github.io/materialxMaterials/documents/html/index.html">here</a>

<h3>Usage</h3>

Forth-coming...


