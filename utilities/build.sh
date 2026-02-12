echo "Start Package Install..."
pip install .
echo "Finished Package Install"

echo "Start Updating Package Data..."
pushd .
cd src/materialxMaterials
python -m materialxMaterials polyhaven -fe
python -m materialxMaterials polyhaven -l
cd data
python -m materialxMaterials gpuopen --loadFromPackage 1 --unzip True
python -m materialxMaterials physbased
python -m materialxMaterials acg --saveMaterials True --output ambientCgMaterials/
python -m materialxMaterials acg --loadMaterials ambientCgMaterials/ambientCG_materialsList.json --downloadMaterial "WoodFloor038" --output ambientCgMaterials/
popd
echo "Finished Updating Package Data"