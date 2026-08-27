# 3Dassets.one API Examples

Example data queried from the [3Dassets.one](https://3dassets.one/) search engine API (`/api/v2`).

| File | Description | Query |
| --- | --- | --- |
| `types.json` | List of asset types | `--listTypes=True` |
| `creators.json` | List of asset creators | `--listCreators=True` |
| `search_wood_assets.json` | Query for first 10 items with "wood" | `-q=wood -l=10` |
| `search_marble_assets.json` | Query for first 10 items with "marble" | `-q=marble -l=10` |
| `search_brick_assets.json` | Query for first 10 items with "brick" | `-q=brick -l=10` |
| `creator_ambientcg_assets.json` | Query for first 10 items by creator "ambientcg" | `-c=ambientcg -l=10` |
| `creator_polyhaven_assets.json` | Query for first 10 items by creator "polyhaven" | `-c=polyhaven -l=10` |
| `type_hdri_assets.json` | Query for first 10 items of type "hdri" | `-t=hdri -l=10` |
| `type_3d_model_assets.json` | Query for first 10 items of type "3d-model" | `-t=3d-model -l=10` |
| `search_brick_polyhaven_pbr_assets.json` | Query for first 10 items with combined filters | `-q=brick -c=polyhaven -t=pbr-material -l=10` |
| `ids_1_2_349_assets.json` | Query for specific asset ids 1, 2, 349 | `-id=1,2,349` |
| `assets_feed.xml` | RSS feed of newly indexed assets | `--downloadRSS=True` |
