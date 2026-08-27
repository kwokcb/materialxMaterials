# Run from root of project
# ========================
# 1. Build example data for the 3Dassets.one asset search API:
pushd .
# Create the output folder
mkdir -p examples/assetOne

# 1a. Create the README header describing the generated example files
cat > examples/assetOne/README.md << 'README_EOF'
# 3Dassets.one API Examples

Example data queried from the [3Dassets.one](https://3dassets.one/) search engine API (`/api/v2`).

| File | Description | Query |
| --- | --- | --- |
README_EOF

# 1b. Query asset types
python3 src_test/assetOneCmd.py --listTypes=True -o examples/assetOne -st types.json
cat >> examples/assetOne/README.md << 'README_EOF'
| `types.json` | List of asset types | `--listTypes=True` |
README_EOF

# 1c. Query creators
python3 src_test/assetOneCmd.py --listCreators=True -o examples/assetOne -sc creators.json
cat >> examples/assetOne/README.md << 'README_EOF'
| `creators.json` | List of asset creators | `--listCreators=True` |
README_EOF

# 1d. Search by keyword / tag
python3 src_test/assetOneCmd.py -q=wood -l=10 -o examples/assetOne -sa search_wood_assets.json
cat >> examples/assetOne/README.md << 'README_EOF'
| `search_wood_assets.json` | Query for first 10 items with "wood" | `-q=wood -l=10` |
README_EOF

python3 src_test/assetOneCmd.py -q=marble -l=10 -o examples/assetOne -sa search_marble_assets.json
cat >> examples/assetOne/README.md << 'README_EOF'
| `search_marble_assets.json` | Query for first 10 items with "marble" | `-q=marble -l=10` |
README_EOF

python3 src_test/assetOneCmd.py -q=brick -l=10 -o examples/assetOne -sa search_brick_assets.json
cat >> examples/assetOne/README.md << 'README_EOF'
| `search_brick_assets.json` | Query for first 10 items with "brick" | `-q=brick -l=10` |
README_EOF

# 1e. Filter by creator (using slugs from the creators list)
python3 src_test/assetOneCmd.py -c=ambientcg -l=10 -o examples/assetOne -sa creator_ambientcg_assets.json
cat >> examples/assetOne/README.md << 'README_EOF'
| `creator_ambientcg_assets.json` | Query for first 10 items by creator "ambientcg" | `-c=ambientcg -l=10` |
README_EOF

python3 src_test/assetOneCmd.py -c=polyhaven -l=10 -o examples/assetOne -sa creator_polyhaven_assets.json
cat >> examples/assetOne/README.md << 'README_EOF'
| `creator_polyhaven_assets.json` | Query for first 10 items by creator "polyhaven" | `-c=polyhaven -l=10` |
README_EOF

# 1f. Filter by asset type (using slugs from the types list)
python3 src_test/assetOneCmd.py -t=hdri -l=10 -o examples/assetOne -sa type_hdri_assets.json
cat >> examples/assetOne/README.md << 'README_EOF'
| `type_hdri_assets.json` | Query for first 10 items of type "hdri" | `-t=hdri -l=10` |
README_EOF

python3 src_test/assetOneCmd.py -t=3d-model -l=10 -o examples/assetOne -sa type_3d_model_assets.json
cat >> examples/assetOne/README.md << 'README_EOF'
| `type_3d_model_assets.json` | Query for first 10 items of type "3d-model" | `-t=3d-model -l=10` |
README_EOF

# 1g. Combined keyword, creator and type filters
python3 src_test/assetOneCmd.py -q=brick -c=polyhaven -t=pbr-material -l=10 -o examples/assetOne -sa search_brick_polyhaven_pbr_assets.json
cat >> examples/assetOne/README.md << 'README_EOF'
| `search_brick_polyhaven_pbr_assets.json` | Query for first 10 items with combined filters | `-q=brick -c=polyhaven -t=pbr-material -l=10` |
README_EOF

# 1h. Query specific asset ids
python3 src_test/assetOneCmd.py -id=1,2,349 -o examples/assetOne -sa ids_1_2_349_assets.json
cat >> examples/assetOne/README.md << 'README_EOF'
| `ids_1_2_349_assets.json` | Query for specific asset ids 1, 2, 349 | `-id=1,2,349` |
README_EOF

# 1i. Download the RSS feed of newly indexed assets (printed to stdout, so redirect to file)
python3 src_test/assetOneCmd.py --downloadRSS=True > examples/assetOne/assets_feed.xml
cat >> examples/assetOne/README.md << 'README_EOF'
| `assets_feed.xml` | RSS feed of newly indexed assets | `--downloadRSS=True` |
README_EOF

popd
