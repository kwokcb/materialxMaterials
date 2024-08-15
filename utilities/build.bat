@echo --------- Building Examples
cd ../src/materialxMaterials/data
python ../GPUOpenLoaderCmd.py --materialNames=1 --saveMaterials=1 
python ../physicallyBasedMaterialXCmd.py
cd ../../../utilities