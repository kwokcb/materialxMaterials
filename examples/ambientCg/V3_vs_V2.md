## ambientCG API V2 vs V3 Differences

### API Endpoint and Response Differences

| Aspect | V2 | V3 |
|---|---|---|
| Asset list endpoint | `/api/v2/downloads_csv` (CSV) | `/api/v3/assets` (JSON) |
| Database endpoint | `/api/v2/full_json` | `/api/v3/assets` |
| Response container | `foundAssets` | `assets` (+ `totalResults`, pagination links) |
| Asset identifier key | `assetId` | `id` |
| Download variants | flat columns `downloadAttribute`, `downloadLink` | nested `downloads[]` array of `{attributes, extension, url, size}` |
| Asset type value | `Material` | `material` |
| Creation method filter | `method` (e.g. `PBRPhotogrammetry`) | `technique` (e.g. `surface-photogrammetry`) |
| `sort` values | `Alphabet`, `Popular`, `Latest`, `Downloads` | `alphabet`, `popular`, `latest`, `downloads`, `oldest`, `random` |
| `include` vocabulary | `statisticsData`, `downloadData`, etc. | `downloads`, `title`, `type`, `maps`, `previews`, etc. |
| Pagination | `limit` ≤ 250 | `limit` ≤ 500 + `offset` (default 100/page) |

### Code Logic Branches (`ambientCGLoader.py`)

| File / area | Change |
|---|---|
| `AmbientCGLoader.__init__` | Includes an `api_version` parameter, and currently defaults to `v3` |
| `setApiVersion()` | Method to switch V2/V3 at runtime (defaults `v3`) |
| `getMaterialNames()` / `findMaterial()` | Default id key is  `id` (for V3) and `assetId` (for V2) when `key=None` |
| `downloadMaterialAsset()` | V3 reads nested `downloads[]` (`attributes`/`url`); V2 keeps flat `downloadAttribute`/`downloadLink` lookup |
| `downloadMaterialsList()` | Dispatches V3 to new JSON endpoint; V2 keeps CSV path |
| `_downloadMaterialsListV3()` / `_fetchAssetsV3()` | V3 specific methods to fetch assets with *pagination* |
| `downloadAssetDatabase()` | V3 uses `/api/v3/assets` + pagination, stores `assets` container; V2 keeps `/full_json` + `foundAssets` |

### Command Access (`ambientCGLoaderCmd.py`)

| File / area | Change |
|---|---|
| `--apiVersion` / `-av` | Version option, defaults to `v3`, passed through to the loader |

### Notes

- V2 is is deprecated*; V3 is the current default, V2 remains available via `-av v2` / `api_version='v2'`.
- Data artifacts (`ambientCG_materialsList.json`, `ambientCG_database.json`) are currently regenerated in V3 format.
