Zone Alignment Report

Previous Labels:
- ELECTRONICS
- GROCERY

Replacement Labels (preferred):
- MAKEUP
- SKINCARE
- BATH_AND_BODY
- BILLING_AREA

Fallback / neutral labels (when department cannot be reliably inferred):
- ZONE_A
- ZONE_B
- BILLING_AREA

Reason For Change:
- The project dataset (CSV under `CCTV Footage`) contains beauty-retail departments (e.g., `makeup`, `skin`, `bath-and-body`). Legacy demo labels like `ELECTRONICS` and `GROCERY` are retail categories that do not match the Purplle beauty-retail dataset and cause incorrect dashboard labeling.
- Aligning the dashboard to dataset department names (or neutral zone names) prevents business confusion and preserves analytics accuracy.

Actions Required (do NOT apply yet — identification only):
1. Remove `ELECTRONICS` and `GROCERY` from `app/services/heatmap_service.py` (update `LEGACY_ZONE_LABELS`).
2. Replace them with dataset-aligned mappings or neutral fallback names. Example mapping:
   - map legacy `ELECTRONICS` -> `ZONE_A` (or `MAKEUP` if camera/zone mapping confirms)
   - map legacy `GROCERY` -> `ZONE_B` (or `SKINCARE`/`BATH_AND_BODY` as appropriate)
3. Update unit tests (e.g., `tests/test_heatmap_labels.py`) to use dataset-aligned sample `zone_id` values or neutral `ZONE_A`/`ZONE_B`.
4. Re-run search to confirm zero occurrences in production code (tests and docs may still reference legacy names).

Validation Checklist (post-change):
- Search repository for `electronics`, `grocery`, `ELECTRONICS`, `GROCERY` → zero occurrences in production code (`app/`, `pipeline/`, `services/`, `api/`).
- Heatmap API (`GET /stores/{store_id}/heatmap`) returns only dataset-aligned or neutral zone labels.
- Tests updated and passing.

Current status (before any changes):
- Legacy labels remain in production mapping: `app/services/heatmap_service.py` (LEGACY_ZONE_LABELS).
- Tests referencing legacy zone names: `tests/test_heatmap_labels.py`.
- CSV dataset does not contain `electronics`/`grocery` department values; it contains `dep_name` like `makeup`, `skin`, `bath-and-body`.

Confirmation Requirement:
- After the removal/change steps above have been applied, re-run a repo search and update this file to state: "No legacy Electronics/Grocery labels remain in the dashboard."