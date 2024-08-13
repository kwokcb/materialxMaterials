# MaterialX Materials

### Introduction

Welcome to MaterialX Materials.

This site hosts a set of libraries and command line utilities to
query remote databases for MaterialX materials.

The current utilities will work with the:

1. PhysicallyBased material database: Material descriptions can be downloaded with additional utilities
to create materials using either: Autodesk Standard Surface, OpenPBR, or glTF PBR shading model shaders. 

2. The AMD GPUOpen material database: MaterialX packages can be downloaded (as zip files). Images and MaterialX
documents can be extracted for any of the posted materials in the database.

Each currently has Python implementations. The PhysicallyBased database has a Javascript implementation
which is used by a <a href="https://kwokcb.github.io/MaterialXLab/javascript/PhysicallyBasedMaterialX_out.html" target="_blank">
interactive page</a>.

### Examples

Documentation forth-coming...

### Dependencies

The Python utilities require:

1. The MaterialX 1.39 or greater package for PhysicallyBased OpenPBR shader creation
2. The `requests` package.

### Building

The repository can be cloned and the package built using:

```
pip install .
```
This will pull down the dependent packages as needed.

### API Reference

The API reference can be found <a href="https://kwokcb.github.io/materialXMaterialx/doc/html/index.html">here</a>

### Usage

Documentation forth-coming...


