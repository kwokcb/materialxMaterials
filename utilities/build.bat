@echo ---------- Build
cd ..
pip install . --quiet
cd utilities
@echo --------- Building Examples
cd ../src/materialxMaterials/data
python ../GPUOpenLoaderCmd.py --materialNames=1 --saveMaterials=1 
python ../physicallyBasedMaterialXCmd.py
python ../ambientCGLoaderCmd.py --saveMaterials True --output ambientCgMaterials/
python ../ambientCGLoaderCmd.py --loadMaterials ambientCgMaterials/ambientCG_materialsList.json --downloadMaterial "WoodFloor038" --output ambientCgMaterials/
cd ../../../utilities