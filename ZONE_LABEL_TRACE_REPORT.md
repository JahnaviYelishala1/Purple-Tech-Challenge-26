Label: ELECTRONICS
Source: Hardcoded legacy mapping in `app/services/heatmap_service.py` (LEGACY_ZONE_LABELS)
File: app/services/heatmap_service.py
Line: 9 ("\"ELECTRONICS\": \"Zone A\",")
Used By: `HeatmapService._display_zone_label` and `HeatmapService.get_store_heatmap`
Dashboard Section: Zone/Heatmap (API: `GET /stores/{store_id}/heatmap` implemented in `app/api/heatmap.py`)
Safe To Remove? YES (production use: YES) — tests reference this label and must be updated.

Trace (full path):
- Database/CSV/Seed: `Event.zone_id` values can originate from ingestion/seed/tests. In this repo, the demo seeder (`app/db/demo_seed.py`) does NOT produce "electronics"; however the unit test `tests/test_heatmap_labels.py` inserts `Event` rows with `zone_id="electronics"` (test lines ~18).
- Service Layer: `HeatmapService.get_store_heatmap` queries `Event.zone_id` and uppercases it; `HeatmapService._display_zone_label` looks up that uppercased string in `LEGACY_ZONE_LABELS` and returns the mapped display label (e.g., "Zone A").
- API Response: `app/api/heatmap.py` returns the `StoreHeatmapResponse` built by `HeatmapService`.
- Dashboard Visualization: dashboard UI consumes `/stores/{store_id}/heatmap` and displays the `zone_id` returned by the API.

Occurrences found in repository (current state):
- app/services/heatmap_service.py: mapping definition at line 9 (production code).
- tests/test_heatmap_labels.py: test inserts `zone_id="electronics"` at line 18 (unit test verifying normalization).
- venv third-party files (matplotlib tests) contain unrelated strings — not part of this project.

Recommended origin classification:
- Primary origin: Hardcoded legacy mapping (production code) + test usage (seeded test rows).
- CSV-derived departments: NONE found mapping to ELECTRONICS in `CCTV Footage` CSV (CSV uses beauty-retail departments like `makeup`, `skin`, `bath-and-body`).

---

Label: GROCERY
Source: Hardcoded legacy mapping in `app/services/heatmap_service.py` (LEGACY_ZONE_LABELS)
File: app/services/heatmap_service.py
Line: 10 ("\"GROCERY\": \"Zone B\",")
Used By: `HeatmapService._display_zone_label` and `HeatmapService.get_store_heatmap`
Dashboard Section: Zone/Heatmap (API: `GET /stores/{store_id}/heatmap` implemented in `app/api/heatmap.py`)
Safe To Remove? YES (production use: YES) — tests reference this label and must be updated.

Trace (full path):
- Database/CSV/Seed: `Event.zone_id` values can originate from ingestion/seed/tests. In this repo, `tests/test_heatmap_labels.py` inserts `zone_id="grocery"` at line 30.
- Service Layer: `HeatmapService.get_store_heatmap` uppercases `Event.zone_id`; `_display_zone_label` maps `GROCERY` to "Zone B" via `LEGACY_ZONE_LABELS`.
- API Response: `app/api/heatmap.py` returns the `StoreHeatmapResponse` which is shown in the dashboard.
- Dashboard Visualization: the dashboard displays the zone labels from the API.

Occurrences found in repository (current state):
- app/services/heatmap_service.py: mapping definition at line 10 (production code).
- tests/test_heatmap_labels.py: test inserts `zone_id="grocery"` at line 30 (unit test verifying normalization).

Recommended origin classification:
- Primary origin: Hardcoded legacy mapping (production code) + test usage (seeded test rows).
- CSV-derived departments: NONE found mapping to GROCERY in `CCTV Footage` CSV.

Notes & Next Steps (no changes applied in this pass):
- The canonical, production location to remove/replace these legacy labels is `app/services/heatmap_service.py` (update `LEGACY_ZONE_LABELS`).
- Tests referencing `electronics`/`grocery` should be updated to use dataset-aligned names (e.g., `makeup`, `skin`, or neutral `ZONE_A`/`ZONE_B`) after production changes are made.
- I did not modify any code as requested. The two report files document exact occurrences and trace paths.
