# Run from root of project
# ========================
# 1. Build example page for PolyHaven materiaals:
pushd .
cd examples/PolyHaven
python -m materialxMaterials polyhaven -id polystyrene -x
python -m materialxMaterials polyhaven -id aerial_rocks_02 -x
python -m materialxMaterials polyhaven -id aerial_beach_02 -x
python -m materialxMaterials polyhaven -id wood_trunk_wall -x
python -m materialxMaterials polyhaven -id aerial_asphalt_01 -x
python ../../utilities/render_materialx.py . -e "--drawEnvironment false" -r 512
popd
