echo "Start Package Install..."
pip install .
echo "Finished Package Install"

echo "Start Updating Package Data..."

echo Download material information from GPUOpen
echo -------------------------------------------------
python -m materialxMaterials gpuopen --output src/materialxMaterials/data/GPUOpenMaterialX/ --materialNames 1 --saveMaterials 1
echo -------------------------------------------------

echo Download material information from PolyHaven
echo -------------------------------------------------
python -m materialxMaterials polyhaven -fe --data_folder src/materialxMaterials/data/PolyHavenMaterialX
echo -------------------------------------------------

echo Download material information from PhysicallyBased
echo -------------------------------------------------
python -m materialxMaterials physbased -nd 1 -wr 1 -o src/materialxMaterials/data/PhysicallyBasedMaterialX/
echo -------------------------------------------------

echo Download material information from AmbientCG
echo -------------------------------------------------
python -m materialxMaterials acg --saveMaterials True --output src/materialxMaterials/data/ambientCgMaterials/ -dd 1
echo -------------------------------------------------

echo "Finished Updating Package Data"



