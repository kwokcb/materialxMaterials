echo "Start Package Install..."
pip install .
echo "Finished Package Install"

echo "Start Updating Package Data..."
pushd .
cd src/materialxMaterials
python -m materialxMaterials polyhaven -fe --data_folder data/PolyHavenMaterialX
python -m materialxMaterials polyhaven -l --data_folder ./data/PolyHavenMaterialX -id polystyrene -x
cd data
python -m materialxMaterials gpuopen --loadFromPackage 1 --unzip True
python -m materialxMaterials physbased
python -m materialxMaterials acg --saveMaterials True --output ambientCgMaterials/
python -m materialxMaterials acg --loadMaterials ambientCgMaterials/ambientCG_materialsList.json --downloadMaterial "WoodFloor038" --output ambientCgMaterials/
popd
cd examples/PolyHaven
python -m materialxMaterials polyhaven -id aerial_rocks_02 -x
python -m materialxMaterials polyhaven -id aerial_beach_02 -x


echo "Finished Updating Package Data"