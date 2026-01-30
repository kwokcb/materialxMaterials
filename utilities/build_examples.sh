# Run from root of project
# ========================
# 1. Build example page for PB:
pushd .
cd examples/PhysicallyBasedMaterialX
# 1a. Generate material files
python -m materialxMaterials physbased -o . -s 1
# 1b. Render files. Note on Windows MaterialX view is unpredictable for size. 512 seems to be "safe" but will produce
# 2048px square images. 
python ../../utilities/render_materialx.py . -e "--drawEnvironment true" -r 512
# 1c. Build summary page
python ../../utilities/renderView.py -t
popd
