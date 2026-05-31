# Dashboard Alignment Report

## Final Zone Names

The dashboard now presents only dataset-safe, camera-aligned zone labels:

- `Zone A`
- `Zone B`
- `Billing Area`
- `Entrance`
- `Exit`

These labels are derived from event data and the configured camera roles, not from fantasy merch categories.

## Final Funnel Stages

The dashboard funnels now align to real event-backed analytics:

- `Store Entry`
- `Zone Engagement`
- `Billing Queue`
- `Completed Purchase`

Notes:
- `Entry` and `Reentry` are handled in the backend arrival logic, with re-entry folded into the arrival stage for funnel continuity.
- `Billing Queue` is tied to `BILLING_QUEUE_JOIN`.
- No dashboard copy now references `Billing Interest`.

## Camera-to-Zone Mapping

Documented dashboard alignment mapping:

- `CAM1` -> `Zone A`
- `CAM2` -> `Zone B`
- `CAM3` -> `Entrance`
- `CAM4` -> `Exit`
- `CAM5` -> `Billing Area`

Source notes:
- The active role map is stored in [config/camera_roles.json](config/camera_roles.json).
- The dashboard uses the role-backed API output plus generic display labels instead of fake product-category names.

## Removed Demo Labels

- `electronics`
- `grocery`
- `aisle-a`
- `aisle-b`
- `aisle-c`
- `Billing Interest`

## Removed Seeded Values

- Demo zone categories in [app/db/demo_seed.py](app/db/demo_seed.py)
- Demo zone categories in [pipeline/mock_event_generator.py](pipeline/mock_event_generator.py)
- Dashboard funnel wording in [dashboard/app.py](dashboard/app.py)

## Remaining Assumptions

- True merchandising zone names are not exposed by the current CCTV configuration, so generic zone names are used.
- The dashboard will remain correct as long as future zone events continue to use generic, dataset-backed identifiers.
- If the dataset later provides real semantic zone names, the display labels can be updated without changing the analytics layer.

## Verification Summary

- Dashboard funnel labels now map to real event types.
- Dashboard heatmap labels are normalized from event `zone_id` values.
- Demo/data-loader sources no longer inject fake retail categories into the dashboard.
- Business language is preserved, but only where it is supported by the event stream.
