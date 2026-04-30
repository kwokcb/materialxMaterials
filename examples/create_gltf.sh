# Create PhysicallyBased glb with "grid" of materials
python -m materialxgltf mtlx2gltf --translateShaders True --bakeTextures False --packageBinary True --bakeResolution 1024 --gltfGeomFileName shaderball.gltf PhysicallyBasedMaterialX_GLTF.mtlx --primsPerMaterial 1
