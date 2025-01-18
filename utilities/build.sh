echo "Start Package Install..."
pip install . --quiet
echo "Finished Package Install"

echo "Start Updating Package Data..."
pushd .
cd src/materialxMaterials/data
python -m materialxMaterials gpuopen --materialNames=1 --saveMaterials=1 
python -m materialxMaterials physbased
python -m materialxMaterials acg --saveMaterials True --output ambientCgMaterials/
python -m materialxMaterials acg --loadMaterials ambientCgMaterials/ambientCG_materialsList.json --downloadMaterial "WoodFloor038" --output ambientCgMaterials/
popd
echo "Finished Updating Package Data"