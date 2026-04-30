echo "Download sample materials from GPUOpen..."
pushd .

cd data
python -m materialxMaterials gpuopen --loadFromPackage 1 --extractExpression "Emerald Peaks Wallpaper"
python -m materialxMaterials gpuopen --loadFromPackage 1 --extractExpression "Indigo Palm Wallpaper"
python -m materialxMaterials gpuopen --loadFromPackage 1 --extractExpression "Oliana Blue Painted Wood" --unzip True

echo "Download sample materials from PolyHaven..."
python -m materialxMaterials polyhaven -l --data_folder ./PolyHavenMaterialX -id polystyrene -x
python -m materialxMaterials polyhaven -l --data_folder ./PolyHavenMaterialX -id polystyrene -x -dt blend
python -m materialxMaterials polyhaven -l --data_folder ./PolyHavenMaterialX -id polystyrene -x -dt gltf

echo "Download sample materials from AmbientCg..."
python -m materialxMaterials acg --loadMaterials ../src/materialxMaterials/data/ambientCgMaterials/ambientCG_materialsList.json --downloadMaterial "WoodFloor038" --output ambientCgMaterials/

popd