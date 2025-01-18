echo "Start Package Install..."
pip install . --quiet
echo "Finished Package Install"

echo "Start Updating Package Data..."
pushd .
cd src/materialxMaterials/data
python ../GPUOpenLoaderCmd.py --materialNames=1 --saveMaterials=1 
python ../physicallyBasedMaterialXCmd.py
python ../ambientCGLoaderCmd.py --saveMaterials True --output ambientCgMaterials/
python ../ambientCGLoaderCmd.py --loadMaterials ambientCgMaterials/ambientCG_materialsList.json --downloadMaterial "WoodFloor038" --output ambientCgMaterials/
popd
echo "Finished Updating Package Data"